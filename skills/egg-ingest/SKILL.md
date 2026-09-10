---
name: egg-ingest
description: >-
  Write items into a Egg library — import bookmarks or any image source,
  scan them with Claude, and distil hearted items into a taste skill. Load
  this before touching a Egg library folder from an agent or script.
---

# Egg ingest — the agent contract

Anything that writes valid items into the library folder is an importer,
including you. This file is the whole contract.

## Where the library is

1. `$EGG_LIBRARY` if set, else
2. `defaults read com.feedegg.egg LibraryPath`, else
3. `~/Library/Application Support/Egg/Library`

Inside it: `items.json` (an array of items), `folders.json` (an overlay of
folder membership — not yours, see rules), and `media/` (the files).

## The item schema

One full example. Required fields: `id`, `file`, `source`, `saved_at`,
`imported_at`. Everything else may be `null`, `""`, or `[]`.

```json
{
 "id": "x_1957533895580074389_0",
 "file": "media/x_1957533895580074389_0.jpg",
 "video": null,
 "source": "x",
 "url": "https://x.com/someone/status/1957533895580074389",
 "author": "someone",
 "text": "the post text, links stripped",
 "alt_text": "",
 "media_type": "photo",
 "saved_at": "2025-08-18T20:31:02.000Z",
 "imported_at": "2025-08-19T09:12:44Z",
 "tags": [],
 "note": "",
 "scan": null
}
```

- `id` — unique, stable, prefixed by source (`x_<postid>_<mediaindex>`,
  `folder_<hash>`, …). The app and scripts dedupe on it.
- `file` — a path relative to the library root, always under `media/`.
  A poster/still image; every item has one, even videos.
- `video` — relative path to an mp4 if the item is motion, else `null`.
- `source` — where it came from: `x`, `arena`, `pinterest`, `folder`,
  `url`, … Pick one word and keep it consistent.
- `saved_at` — when the user saved it at the source (ISO 8601).
  `imported_at` — when you wrote it here.
- `scan` — leave `null`; `scan.py` fills it. Structure when present:
  `{description, style: [..], subjects: [..], colors: [{name, hex}], text}`.

## Rules

- Write media into `media/` with a filename derived from the item id or a
  content hash — never a name that can collide.
- Hold an exclusive `flock` on `.items.lock` across read → merge → write temp
  → rename of `items.json`. Use `scripts/library_io.py:merge_items` so scans,
  desktop feed imports, and edits cannot overwrite one another. Never save
  a stale snapshot or truncate-then-write.
- **Never touch `folders.json`.** Hearts and hides are the user's curation;
  clobbering them destroys the signal the taste skill is built from.
- Never overwrite an existing item's `scan`, `tags`, or `note`. Merging means
  adding new items and (only) filling missing `video` on existing ones.
- Preserve fields you don't recognise — other tools may have added them.

## Running the existing importers

They live in `scripts/` in this repo. Python 3.9+, standard library only.

```bash
# X bookmarks (OAuth PKCE, browser window opens). The client id is the
# user's own — from their X developer app; ALPHA.md has the 3-minute
# setup. Never use a shared or shipped client id.
X_CLIENT_ID=<the user's own client id> python3 scripts/fetch_bookmarks.py

# Full-history backfill (the bookmarks API caps out):
#   1. paste scripts/harvest_bookmark_ids.js into the console on
#      x.com/i/bookmarks (read its header), get bookmark-ids.json
#   2. hydrate — --survey first to see cost, --since to bound it:
X_CLIENT_ID=... python3 scripts/import_ids.py ~/Downloads/bookmark-ids.json

# Make everything searchable (safe to interrupt and re-run):
ANTHROPIC_API_KEY=sk-ant-... python3 scripts/scan.py
```

## Writing a new importer

Three steps: get media files into `media/`, build item dicts, merge-append
into `items.json`. Save this template in `scripts/`, beside `library_io.py`:

```python
#!/usr/bin/env python3
"""Import images from a local folder into the Egg library."""
import hashlib, json, os, shutil, subprocess, sys, time
from pathlib import Path
from library_io import merge_items

def library():
    if os.environ.get("EGG_LIBRARY"):
        return Path(os.environ["EGG_LIBRARY"]).expanduser()
    r = subprocess.run(["defaults", "read", "com.feedegg.egg", "LibraryPath"],
                       capture_output=True, text=True)
    if r.returncode == 0 and r.stdout.strip():
        return Path(r.stdout.strip())
    return Path.home() / "Library/Application Support/Egg/Library"

LIB = library(); MEDIA = LIB / "media"; ITEMS = LIB / "items.json"
MEDIA.mkdir(parents=True, exist_ok=True)
existing = {i["id"]: i for i in json.loads(ITEMS.read_text())} if ITEMS.exists() else {}
new = []
for src in Path(sys.argv[1]).glob("*.[jp][pn]g"):
    digest = hashlib.sha256(src.read_bytes()).hexdigest()[:16]
    item_id = f"folder_{digest}"
    if item_id in existing: continue
    fname = f"{item_id}{src.suffix.lower()}"
    shutil.copy2(src, MEDIA / fname)
    now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    new.append({"id": item_id, "file": f"media/{fname}", "video": None,
                "source": "folder", "url": None, "author": "",
                "text": "", "alt_text": "", "media_type": "photo",
                "saved_at": now, "imported_at": now,
                "tags": [], "note": "", "scan": None})
merge_items(ITEMS, new)
print(f"{len(new)} new items. Next: python3 scripts/scan.py")
```

## The taste skill

Heart things in Egg first (50+ makes it worth reading), then:

```bash
ANTHROPIC_API_KEY=sk-ant-... python3 scripts/make_skill.py --dry-run   # cost preview
ANTHROPIC_API_KEY=sk-ant-... python3 scripts/make_skill.py
```

The skill lands in `.claude/skills/light-table-taste/` at this repo's root
(rename with `--name`). It's a project skill: Claude Code picks it up in any
repo you copy it into. Re-run after hearting more; per-image readings are
cached in the library's `taste.json`.
