"""Cooperative, atomic items.json writes shared with the desktop importer."""
import fcntl
import json
import os
import tempfile
from pathlib import Path


def merge_items(path, additions=(), *, scans=None, videos=None):
    """Merge only this operation's changes into the latest on-disk records.

    Every writer holds .items.lock across read/merge/rename. In particular,
    a scanner must not save its hours-old snapshot over newly imported items
    or a user's tags and notes. Existing unknown fields survive unchanged.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with (path.parent / ".items.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        items = json.loads(path.read_text()) if path.exists() else []
        if not isinstance(items, list):
            raise ValueError("items.json must contain an array")
        known = {item["id"] for item in items}
        for item in additions:
            if item["id"] not in known:
                items.append(item)
                known.add(item["id"])
        for item in items:
            identity = item["id"]
            if scans and identity in scans:
                item["scan"] = scans[identity]
            if videos and videos.get(identity) and not item.get("video"):
                item["video"] = videos[identity]
        fd, temporary = tempfile.mkstemp(dir=path.parent, prefix=".items-", suffix=".json")
        try:
            with os.fdopen(fd, "w") as output:
                json.dump(items, output, indent=1)
                output.flush()
                os.fsync(output.fileno())
            os.replace(temporary, path)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)
        return items
