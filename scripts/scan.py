#!/usr/bin/env python3
"""
Scan library visuals with Claude vision to make them searchable.

For each unscanned image, generates:
  - a one-sentence description
  - style descriptors (e.g. "brutalist", "hand-drawn", "editorial")
  - subject tags (what's actually in it)
  - dominant colors (named + hex)
  - any visible text

Run:  ANTHROPIC_API_KEY=sk-... python3 scan.py
Options:
  --rescan        re-scan everything, including already-scanned items
  --limit N       scan at most N items this run
  --workers N     how many images to scan at once (default 4)

Items are scanned newest-saved first, checkpointed every 25, and skipped if
already scanned — so interrupting and re-running is always safe.
"""

import base64
import json
import mimetypes
import os
import subprocess
import sys
import threading
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from library_io import merge_items

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

API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
# Sonnet 5 supports structured outputs, which Sonnet 4.6 does not. The schema
# guarantees style/subjects/colors arrive as lists — one earlier scan returned
# "style": "minimal" as a bare string, which was enough to crash the app's
# filter rail. (The ~1.5% of items that used to fail were a separate problem:
# max_tokens truncation, fixed below.)
MODEL = os.environ.get("LT_MODEL", "claude-sonnet-5")

SCHEMA = {
    "type": "object",
    "properties": {
        "description": {"type": "string"},
        "style": {"type": "array", "items": {"type": "string"}},
        "subjects": {"type": "array", "items": {"type": "string"}},
        "colors": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {"name": {"type": "string"},
                               "hex": {"type": "string"}},
                "required": ["name", "hex"],
                "additionalProperties": False,
            },
        },
        "text": {"type": "string"},
    },
    "required": ["description", "style", "subjects", "colors", "text"],
    "additionalProperties": False,
}

PROMPT = """You are indexing an image for a designer's visual inspiration library.
Respond ONLY with a JSON object, no markdown fences, with these keys:
- "description": one vivid sentence describing the image
- "style": 3-6 lowercase style/aesthetic descriptors (e.g. "brutalist", "pastel", "editorial", "hand-drawn", "retro-futurist")
- "subjects": 2-6 lowercase tags for what the image contains (e.g. "typography", "poster", "interior", "packaging", "ui")
- "colors": 2-5 dominant colors, each as {"name": "...", "hex": "#..."}
- "text": any legible text in the image, or ""
"""


class OutOfCredit(Exception):
    """Anthropic balance exhausted — retrying other items is pointless."""


class Refused(Exception):
    """Safety classifiers declined this image. Retrying won't help."""


# X serves media at URLs whose extension doesn't always match the bytes — a
# PNG delivered from a .jpg path is common. Declaring the wrong media_type is
# a hard 400, so trust the magic bytes over the filename.
MAGIC = [
    (b"\xff\xd8\xff", "image/jpeg"),
    (b"\x89PNG\r\n\x1a\n", "image/png"),
    (b"GIF8", "image/gif"),
]


def sniff_mime(path, head):
    for sig, mime in MAGIC:
        if head.startswith(sig):
            return mime
    if head[:4] == b"RIFF" and head[8:12] == b"WEBP":
        return "image/webp"
    return mimetypes.guess_type(str(path))[0] or "image/jpeg"


def call_claude(img_path):
    raw = img_path.read_bytes()
    if not raw:
        raise RuntimeError("file is empty (0 bytes) — re-download it")
    mime = sniff_mime(img_path, raw[:16])
    data = base64.b64encode(raw).decode()
    body = json.dumps({
        "model": MODEL,
        # Text-heavy images produce a long "text" field. At 600 the response
        # was truncated mid-string and the JSON never parsed (~1.5% of items).
        "max_tokens": 2000,
        "output_config": {"format": {"type": "json_schema", "schema": SCHEMA}},
        "messages": [{
            "role": "user",
            "content": [
                {"type": "image",
                 "source": {"type": "base64", "media_type": mime, "data": data}},
                {"type": "text", "text": PROMPT},
            ],
        }],
    }).encode()
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages", data=body,
        headers={
            "Content-Type": "application/json",
            "x-api-key": API_KEY,
            "anthropic-version": "2023-06-01",
        })
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req) as r:
                resp = json.loads(r.read())
            if resp.get("stop_reason") == "refusal":
                cat = (resp.get("stop_details") or {}).get("category", "?")
                raise Refused(f"declined by safety classifier ({cat})")
            text = "".join(b.get("text", "") for b in resp["content"])
            text = text.replace("```json", "").replace("```", "").strip()
            return json.loads(text)
        except urllib.error.HTTPError as e:
            if e.code in (429, 529):
                time.sleep(15 * (attempt + 1))
                continue
            # Surface the API's message. "HTTP Error 400: Bad Request" alone
            # is indistinguishable between a bad image and an empty wallet.
            detail = ""
            try:
                detail = json.loads(e.read()).get("error", {}).get("message", "")
            except Exception:
                pass
            if "credit balance" in detail.lower():
                raise OutOfCredit(detail)
            raise RuntimeError(f"HTTP {e.code}: {detail or e.reason}")
        except Refused:
            raise
        except json.JSONDecodeError:
            if attempt < 3:
                continue
            raise
    return None


def main():
    if not API_KEY:
        print("error: set ANTHROPIC_API_KEY", file=sys.stderr)
        sys.exit(1)
    if not ITEMS.exists():
        print("error: no library/items.json — run fetch_bookmarks.py first",
              file=sys.stderr)
        sys.exit(1)

    rescan = "--rescan" in sys.argv
    limit = None
    if "--limit" in sys.argv:
        limit = int(sys.argv[sys.argv.index("--limit") + 1])

    workers = 4
    if "--workers" in sys.argv:
        workers = max(1, int(sys.argv[sys.argv.index("--workers") + 1]))

    items = json.loads(ITEMS.read_text())
    todo = [it for it in items if rescan or not it.get("scan")]
    # Newest first, so the posts you saved most recently become searchable
    # early instead of after a full pass over the archive.
    todo.sort(key=lambda it: it.get("saved_at", ""), reverse=True)
    if limit:
        todo = todo[:limit]
    print(f"{len(todo)} items to scan, {workers} at a time")

    lock = threading.Lock()
    state = {"done": 0, "failed": 0}
    scans = {}
    total = len(todo)

    def work(it):
        if state.get("abort"):
            return
        path = LIB / it["file"]
        if not path.exists():
            with lock:
                print(f"  missing file, skipping: {it['file']}")
            return
        try:
            scan = call_claude(path)
        except OutOfCredit as e:
            # Stop the whole run rather than marching the rest of the queue
            # through the same guaranteed failure.
            with lock:
                if not state.get("abort"):
                    state["abort"] = True
                    print(f"\n  OUT OF CREDIT — stopping.\n  {e}")
            return
        except Exception as e:
            with lock:
                state["failed"] += 1
                print(f"  {it['file']} failed: {e}")
            return
        if not scan:
            with lock:
                state["failed"] += 1
                print(f"  {it['file']} failed")
            return
        # Only the shared list and the counter need guarding; the API call
        # above is the slow part and runs outside the lock.
        with lock:
            it["scan"] = scan
            scans[it["id"]] = scan
            state["done"] += 1
            n = state["done"]
            if n % 25 == 0 or n == total:
                merge_items(ITEMS, scans=scans)
                print(f"  {n}/{total} scanned "
                      f"({state['failed']} failed) — saved")

    try:
        with ThreadPoolExecutor(max_workers=workers) as pool:
            list(pool.map(work, todo))
    except KeyboardInterrupt:
        print("\ninterrupted — saving what finished")

    merge_items(ITEMS, scans=scans)
    print(f"\nDone. Scanned {state['done']} items, {state['failed']} failed.")
    if state["failed"]:
        print("Re-run to retry the failures — they stay unscanned.")
    print("Next: open Egg — the new items are searchable there.")


if __name__ == "__main__":
    main()
