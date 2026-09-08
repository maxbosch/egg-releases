#!/usr/bin/env python3
"""
Import bookmarks that the bookmarks API won't return, using a list of IDs
harvested from the web UI.

The bookmarks endpoint caps what it returns. The lookup endpoint does not —
so we collect IDs in the browser (harvest_bookmark_ids.js) and hydrate them
here, 100 at a time.

Usage:
  1. Run harvest_bookmark_ids.js in the browser (see that file's header)
  2. X_CLIENT_ID=... python3 import_ids.py ~/Downloads/bookmark-ids.json

Already-imported posts are skipped, so this is safe to re-run and safe to
run after fetch_bookmarks.py. Scans, tags and notes are never touched.
"""

import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
from pathlib import Path
from library_io import merge_items

import fetch_bookmarks as fb   # reuse auth, paging, download, variant picking

BATCH = 100   # max ids per /2/tweets lookup


def api_get_fresh(token_box, path, params):
    """fb.api_get, but survives the access token expiring mid-run.

    X access tokens last ~2 hours; a large import outlives one easily. On a
    401 we force a refresh with the stored refresh_token and retry once.
    """
    try:
        return fb.api_get(token_box[0], path, params)
    except urllib.error.HTTPError as e:
        if e.code != 401:
            raise
        print("  access token expired — refreshing")
        stored = json.loads(fb.TOKENS.read_text())
        token_box[0] = fb.refresh(stored["refresh_token"])
        return fb.api_get(token_box[0], path, params)


# X post ids are snowflakes: the creation time is encoded in the high bits,
# so we can date a post without asking the API. That matters because X bills
# per post returned — filtering here costs nothing, filtering after the
# lookup costs full price for posts we then throw away.
SNOWFLAKE_EPOCH_MS = 1288834974657


def post_date(post_id):
    """UTC date (YYYY-MM-DD) a post id was created, computed offline."""
    ms = (int(post_id) >> 22) + SNOWFLAKE_EPOCH_MS
    return time.strftime("%Y-%m-%d", time.gmtime(ms / 1000))


def load_ids(path):
    raw = json.loads(Path(path).read_text())
    ids = raw if isinstance(raw, list) else raw.get("ids", [])
    clean = [str(i) for i in ids if str(i).isdigit()]
    if not clean:
        fb.die(f"no numeric post ids found in {path}")
    return list(dict.fromkeys(clean))          # dedupe, keep order


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args:
        fb.die("usage: python3 import_ids.py <bookmark-ids.json> "
               "[--since YYYY-MM-DD] [--survey]")

    survey = "--survey" in sys.argv
    since = ""
    if "--since" in sys.argv:
        since = sys.argv[sys.argv.index("--since") + 1]

    fb.LIB.mkdir(exist_ok=True)
    fb.MEDIA.mkdir(exist_ok=True)

    ids = load_ids(args[0])
    existing = {}
    if fb.ITEMS.exists():
        existing = {it["id"]: it for it in json.loads(fb.ITEMS.read_text())}

    # An item id is x_<postid>_<n>; strip the media index to compare posts.
    have_posts = {k.rsplit("_", 1)[0].removeprefix("x_") for k in existing}
    todo = ids if survey else [i for i in ids if i not in have_posts]

    # Drop old posts BEFORE the lookup — X charges per post returned.
    if since and not survey:
        before = len(todo)
        todo = [i for i in todo if post_date(i) >= since]
        print(f"{before - len(todo)} posts older than {since} skipped "
              f"(no credits spent on them)")

    print(f"{len(ids)} ids harvested")
    if survey:
        print("SURVEY MODE — reading dates only, downloading nothing\n")
    else:
        print(f"{len(have_posts)} posts already in library")
        if since:
            print(f"skipping anything posted before {since}")
        print(f"{len(todo)} to fetch\n")
    if not todo:
        print("Nothing new. Done.")
        return

    token_box = [fb.get_tokens()]   # list so the refresh helper can swap it
    new_items, no_media, missing, too_old = [], 0, 0, 0
    by_year = {}   # survey: year -> [posts, posts_with_media]

    for n in range(0, len(todo), BATCH):
        batch = todo[n:n + BATCH]
        print(f"batch {n // BATCH + 1}/{(len(todo) + BATCH - 1) // BATCH} "
              f"({len(batch)} posts)")
        resp = api_get_fresh(token_box, "/tweets", {
            "ids": ",".join(batch),
            "expansions": "attachments.media_keys,author_id",
            "media.fields": "media_key,type,url,preview_image_url,width,height,"
                            "alt_text,variants",
            "tweet.fields": "created_at,text,entities",
            "user.fields": "username,name",
        })

        # Deleted / protected / suspended posts come back under "errors".
        missing += len(resp.get("errors", []))
        media_by_key = {m["media_key"]: m
                        for m in resp.get("includes", {}).get("media", [])}
        users_by_id = {u["id"]: u
                       for u in resp.get("includes", {}).get("users", [])}

        for t in resp.get("data", []):
            author = users_by_id.get(t.get("author_id"), {})
            keys = t.get("attachments", {}).get("media_keys", [])
            created = t.get("created_at", "")

            if survey:
                y = created[:4] or "?"
                row = by_year.setdefault(y, [0, 0])
                row[0] += 1
                if keys:
                    row[1] += len([k for k in keys if k in media_by_key])
                continue

            # Date filter runs after the lookup but before any download, so
            # skipping an old post costs no bandwidth and no disk.
            if since and created and created[:10] < since:
                too_old += 1
                continue
            if not keys:
                no_media += 1
                continue
            for i, k in enumerate(keys):
                m = media_by_key.get(k)
                if not m:
                    continue
                img_url = m.get("url") or m.get("preview_image_url")
                if not img_url:
                    continue
                item_id = f"x_{t['id']}_{i}"
                if item_id in existing:
                    continue
                ext = os.path.splitext(
                    urllib.parse.urlparse(img_url).path)[1] or ".jpg"
                fname = item_id + ext
                print(f"  {fname}")
                if not fb.download(img_url, fb.MEDIA / fname):
                    continue
                video_rel = None
                vid_url = fb.best_variant(m)
                if vid_url:
                    vname = item_id + ".mp4"
                    if fb.download(vid_url, fb.MEDIA / vname):
                        video_rel = f"media/{vname}"
                clean_text = re.sub(r"https://t\.co/\S+", "",
                                    t.get("text", "")).strip()
                new_items.append({
                    "id": item_id,
                    "file": f"media/{fname}",
                    "video": video_rel,
                    "source": "x",
                    "url": f"https://x.com/{author.get('username','i')}"
                           f"/status/{t['id']}",
                    "author": author.get("username", ""),
                    "text": clean_text,
                    "alt_text": m.get("alt_text", ""),
                    "media_type": m["type"],
                    "saved_at": t.get("created_at", ""),
                    "imported_at": time.strftime("%Y-%m-%dT%H:%M:%SZ",
                                                 time.gmtime()),
                    "tags": [],
                    "note": "",
                    "scan": None,
                })
        # Checkpoint after every batch. Without this a failure anywhere in a
        # long run discards all the metadata fetched so far, and re-fetching
        # costs real money because X bills per post returned.
        if not survey and new_items:
            merge_items(fb.ITEMS, new_items)

        time.sleep(0.5)   # be gentle between batches

    if survey:
        print(f"\n{'year':<6}{'posts':>8}{'media items':>14}{'cumulative':>13}"
              f"{'scan cost':>12}")
        cum = 0
        for y in sorted(by_year, reverse=True):
            posts, media = by_year[y]
            cum += media
            print(f"{y:<6}{posts:>8}{media:>14}{cum:>13}{'$'+format(cum*0.0083, '.0f'):>12}")
        print(f"\n{missing} posts unavailable (deleted, protected or suspended)")
        print("\n'cumulative' = items you get importing that year and newer.")
        print("Re-run with e.g.  --since 2023-01-01  to import just those.")
        return

    merged = merge_items(fb.ITEMS, new_items)
    print(f"\nDone. {len(new_items)} new items, {len(merged)} total.")
    print(f"  {no_media} posts had no image or video (text/link only)")
    print(f"  {missing} posts unavailable (deleted, protected or suspended)")
    if too_old:
        print(f"  {too_old} posts skipped as older than {since}")
    if new_items:
        print("\nNext: python3 scan.py   to index the new ones")


if __name__ == "__main__":
    main()
