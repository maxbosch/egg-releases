#!/usr/bin/env python3
"""
Distil your hearted items into a Claude skill.

Bookmarks are a weak signal — you save things for a dozen reasons. Hearts are
not: they're the subset you'd defend. This reads only those.

Two passes:
  1. READ  — each hearted image, with the questions scan.py never asks.
             scan.py indexes for *search* (style words, subject tags, colour
             names). Taste lives in specifics: the exact off-white, the type
             pairing, the spacing rhythm, what a piece deliberately omits.
             Cached in library/taste.json, so re-runs only read new hearts.
  2. WRITE — synthesise those readings, plus a sample of the actual images,
             into prescriptive rules. Descriptive output ("the collection is
             minimal") is useless; the skill has to say what to *do*.

Run:  ANTHROPIC_API_KEY=sk-... python3 make_skill.py
Options:
  --name NAME     skill directory name (default: light-table-taste)
  --reread        re-read every heart, ignoring the cache
  --workers N     parallel reads (default 4)
  --dry-run       show what would be read, spend nothing
"""

import base64
import json
import os
import subprocess
import sys
import threading
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).parent


def resolve_library():
    """Locate the Egg library. The app owns this setting; scripts follow it.

    1. EGG_LIBRARY env var, if set
    2. the app's LibraryPath default, mirrored so scripts and agents can find it
    3. the default location
    """
    env = os.environ.get("EGG_LIBRARY")
    if env:
        return Path(env).expanduser()
    try:
        r = subprocess.run(["defaults", "read", "com.feedegg.egg", "LibraryPath"],
                           capture_output=True, text=True)
        if r.returncode == 0 and r.stdout.strip():
            return Path(r.stdout.strip()).expanduser()
    except OSError:
        pass
    return Path.home() / "Library" / "Application Support" / "Egg" / "Library"


LIB = resolve_library()
ITEMS = LIB / "items.json"
FOLDERS = LIB / "folders.json"
CACHE = LIB / "taste.json"          # per-image readings, keyed by item id
SKILLS = ROOT.parent / ".claude" / "skills"

API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
READ_MODEL = os.environ.get("LT_READ_MODEL", "claude-sonnet-5")
# The synthesis is one call and it is the whole point — don't economise here.
WRITE_MODEL = os.environ.get("LT_WRITE_MODEL", "claude-opus-5")
HEART = "hearted"
SAMPLE_IMAGES = 18                  # images sent to the synthesis pass

READ_PROMPT = """You are helping a designer articulate their own taste by
studying one piece from their collection.

Do not describe the image generally. Answer only in the specifics another
designer could act on, and be concrete — name actual typefaces if you can
identify them, give real hex values, describe measurable proportions.

Above all: say what is DISTINCTIVE here. Almost every piece of design on the
internet is "clean, minimal, modern" — that is the base rate and it is not
useful. What would a careful observer notice about THIS piece that would not
be true of a generic well-made one?"""

READ_SCHEMA = {
    "type": "object",
    "properties": {
        "typography": {"type": "string"},
        "layout": {"type": "string"},
        "palette": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "hex": {"type": "string"},
                    "role": {"type": "string"},
                },
                "required": ["hex", "role"],
                "additionalProperties": False,
            },
        },
        "surface": {"type": "string"},
        "motion": {"type": "string"},
        "avoids": {"type": "string"},
        "distinctive": {"type": "string"},
    },
    "required": ["typography", "layout", "palette", "surface", "motion",
                 "avoids", "distinctive"],
    "additionalProperties": False,
}

WRITE_PROMPT = """You are writing a Claude Skill that captures one designer's
visual taste, derived from the collection they personally hearted.

You are given: per-piece readings of every hearted item, and a sample of the
actual images. Trust the images over the readings where they disagree.

Write the body of a SKILL.md. Requirements:

- PRESCRIPTIVE, not descriptive. "Use a warm off-white near #F4F1EA for page
  grounds" — not "the collection features warm off-whites." Every line should
  be something a designer could follow.
- SPECIFIC. Real hex values, named typefaces or precise type characteristics,
  actual proportions and spacing relationships. Vague guidance is worse than
  none, because it reads as instruction while carrying no information.
- HONEST ABOUT SPREAD. If the collection holds two or three distinct modes
  rather than one voice, say so and describe each, with when to reach for it.
  Do not average them into mush.
- Include what this taste AVOIDS. Negative space defines a sensibility as much
  as what it embraces.
- Skip anything true of all competent design. If a line would apply equally to
  any well-made page, cut it.

Structure it with these sections, in order:
## The through-line
## Typography
## Colour
## Layout and space
## Surface and depth
## Motion
## What this taste avoids
## Applying it

Respond with the markdown body only. No frontmatter, no preamble."""


def die(msg):
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(1)


def api(model, content, schema=None, max_tokens=2000):
    """Always streams.

    The synthesis pass sends 18 images and asks for 4,000 tokens back; as a
    single blocking request that reliably exceeded the read timeout with
    nothing to show for it. Streaming means the socket sees bytes throughout,
    so the timeout only fires on a genuinely dead connection.
    """
    payload = {"model": model, "max_tokens": max_tokens, "stream": True,
               "messages": [{"role": "user", "content": content}]}
    if schema:
        payload["output_config"] = {"format": {"type": "json_schema",
                                               "schema": schema}}
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json", "x-api-key": API_KEY,
                 "anthropic-version": "2023-06-01"})

    parts = []
    with urllib.request.urlopen(req, timeout=300) as r:
        for raw in r:
            line = raw.decode("utf-8", "replace").strip()
            if not line.startswith("data:"):
                continue
            try:
                ev = json.loads(line[5:].strip())
            except json.JSONDecodeError:
                continue
            kind = ev.get("type")
            if kind == "content_block_delta":
                parts.append(ev.get("delta", {}).get("text", ""))
            elif kind == "message_delta":
                if ev.get("delta", {}).get("stop_reason") == "refusal":
                    raise RuntimeError("declined by safety classifier")
            elif kind == "error":
                raise RuntimeError(ev.get("error", {}).get("message", "stream error"))
    return "".join(parts)


MAGIC = [(b"\xff\xd8\xff", "image/jpeg"), (b"\x89PNG\r\n\x1a\n", "image/png"),
         (b"GIF8", "image/gif")]


def image_block(path):
    raw = path.read_bytes()
    if not raw:
        return None
    mime = next((m for sig, m in MAGIC if raw.startswith(sig)), None)
    if mime is None:
        mime = "image/webp" if raw[:4] == b"RIFF" else "image/jpeg"
    return {"type": "image", "source": {"type": "base64", "media_type": mime,
                                        "data": base64.b64encode(raw).decode()}}


def load_canon():
    if not ITEMS.exists():
        die("no library/items.json — run fetch_bookmarks.py first")
    items = {it["id"]: it for it in json.loads(ITEMS.read_text())}
    folders = json.loads(FOLDERS.read_text()) if FOLDERS.exists() else {}
    ids = folders.get(HEART, [])
    if not ids:
        die("nothing hearted yet.\n"
            "       Open Egg and heart the pieces you'd\n"
            "       defend — 50 or more makes a usable skill. Bookmarks alone\n"
            "       describe your feed; hearts describe your taste.")
    return [items[i] for i in ids if i in items]


def read_pass(canon, workers, reread):
    cache = json.loads(CACHE.read_text()) if CACHE.exists() and not reread else {}
    todo = [it for it in canon if it["id"] not in cache]
    print(f"{len(canon)} hearted · {len(cache)} already read · {len(todo)} to read")
    if not todo:
        return cache

    lock = threading.Lock()
    done = [0]

    def read(it):
        path = LIB / it["file"]
        block = image_block(path) if path.exists() else None
        if not block:
            with lock:
                print(f"  skip (missing or empty): {it['file']}")
            return
        try:
            # Seven prose fields plus a palette: 1200 truncated mid-string
            # and the JSON never parsed — the same trap scan.py fell into.
            out = api(READ_MODEL, [block, {"type": "text", "text": READ_PROMPT}],
                      READ_SCHEMA, 3000)
            reading = json.loads(out)
        except Exception as e:
            with lock:
                print(f"  {it['file']} failed: {e}")
            return
        with lock:
            cache[it["id"]] = reading
            done[0] += 1
            if done[0] % 10 == 0:
                CACHE.write_text(json.dumps(cache, indent=1))
                print(f"  {done[0]}/{len(todo)} read")

    with ThreadPoolExecutor(max_workers=workers) as pool:
        list(pool.map(read, todo))
    CACHE.write_text(json.dumps(cache, indent=1))
    print(f"  {done[0]} read")
    return cache


def write_pass(canon, readings):
    # Spread the image sample across the collection rather than taking the
    # first N, which would over-represent whatever you hearted most recently.
    have = [it for it in canon if it["id"] in readings]
    step = max(1, len(have) // SAMPLE_IMAGES)
    sample = have[::step][:SAMPLE_IMAGES]

    content = []
    for it in sample:
        block = image_block(LIB / it["file"])
        if block:
            content.append(block)
    content.append({"type": "text", "text":
                    "Per-piece readings of the full hearted collection:\n"
                    + json.dumps([readings[it["id"]] for it in have], indent=1)})
    content.append({"type": "text", "text": WRITE_PROMPT})
    print(f"synthesising from {len(have)} readings + {len(sample)} images "
          f"({WRITE_MODEL})…")
    return api(WRITE_MODEL, content, max_tokens=4000)


def palette_reference(readings):
    """Roll every observed colour up into one reference, commonest first."""
    seen = {}
    for r in readings.values():
        for c in r.get("palette") or []:
            hexv = (c.get("hex") or "").strip().lower()
            if not hexv.startswith("#"):
                continue
            e = seen.setdefault(hexv, {"n": 0, "roles": {}})
            e["n"] += 1
            role = (c.get("role") or "").strip().lower()
            e["roles"][role] = e["roles"].get(role, 0) + 1
    rows = sorted(seen.items(), key=lambda kv: -kv[1]["n"])
    out = ["# Palette", "",
           "Every colour observed across the hearted collection, commonest",
           "first. The role is what it was doing in the piece.", "",
           "| hex | uses | usual role |", "| --- | ---: | --- |"]
    for hexv, e in rows[:60]:
        role = max(e["roles"].items(), key=lambda kv: kv[1])[0] if e["roles"] else "—"
        out.append(f"| `{hexv}` | {e['n']} | {role} |")
    return "\n".join(out) + "\n"


def canon_reference(canon, readings):
    out = ["# Canon", "",
           "The hearted pieces this skill was derived from, with what each",
           "contributes. Re-run make_skill.py after hearting more.", ""]
    for it in canon:
        r = readings.get(it["id"])
        if not r:
            continue
        out.append(f"## @{it.get('author') or '—'} · {(it.get('saved_at') or '')[:10]}")
        if it.get("url"):
            out.append(f"{it['url']}")
        out.append(f"- **distinctive**: {r.get('distinctive','')}")
        out.append(f"- **typography**: {r.get('typography','')}")
        out.append(f"- **avoids**: {r.get('avoids','')}")
        out.append("")
    return "\n".join(out)


def main():
    if "--dry-run" not in sys.argv and not API_KEY:
        die("set ANTHROPIC_API_KEY")
    name = "light-table-taste"
    if "--name" in sys.argv:
        name = sys.argv[sys.argv.index("--name") + 1]
    workers = 4
    if "--workers" in sys.argv:
        workers = max(1, int(sys.argv[sys.argv.index("--workers") + 1]))

    canon = load_canon()
    if "--dry-run" in sys.argv:
        cached = json.loads(CACHE.read_text()) if CACHE.exists() else {}
        todo = [it for it in canon if it["id"] not in cached]
        print(f"{len(canon)} hearted, {len(todo)} would be read")
        print(f"estimated cost: ~${len(todo) * 0.011 + 0.30:.2f}")
        return

    readings = read_pass(canon, workers, "--reread" in sys.argv)
    if not readings:
        die("nothing could be read")

    body = write_pass(canon, readings)

    out = SKILLS / name
    (out / "references").mkdir(parents=True, exist_ok=True)
    n = len([1 for it in canon if it["id"] in readings])
    (out / "SKILL.md").write_text(
        "---\n"
        f"name: {name}\n"
        "description: >-\n"
        "  This designer's own visual taste, derived from the pieces they\n"
        "  hearted in their inspiration library. Load before making visual\n"
        "  design decisions for them — layouts, palettes, type, slides,\n"
        "  frontends — so the work matches their sensibility rather than a\n"
        "  generic house style.\n"
        "---\n\n"
        f"<!-- Generated by make_skill.py from {n} hearted pieces. Re-run "
        "after hearting more. -->\n\n"
        + body.strip() + "\n\n"
        "## References\n\n"
        "- `references/palette.md` — every colour observed, with usual role\n"
        "- `references/canon.md` — the source pieces and what each contributes\n")
    (out / "references" / "palette.md").write_text(palette_reference(readings))
    (out / "references" / "canon.md").write_text(canon_reference(canon, readings))

    print(f"\nWrote {out}/SKILL.md  (from {n} pieces)")
    print("  + references/palette.md, references/canon.md")
    print("\nIt's a project skill — Claude Code picks it up in this repo.")
    print("Test it: ask for a landing page here, then in a directory without")
    print("the skill, and compare. If they look the same, it isn't earning its")
    print("place — heart more sharply and re-run.")


if __name__ == "__main__":
    main()
