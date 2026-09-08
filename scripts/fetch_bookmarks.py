#!/usr/bin/env python3
"""
Import your X (Twitter) bookmarks into the local library.

Setup (one time):
  1. Create an app at https://console.x.com
  2. In the app's auth settings, enable OAuth 2.0 with:
       - Type: Native App (public client, PKCE)
       - Callback URL: http://127.0.0.1:8765/callback
       - Scopes: tweet.read users.read bookmark.read offline.access
  3. Copy the Client ID and run:
       X_CLIENT_ID=your_client_id python3 fetch_bookmarks.py

The script opens a browser window for you to authorize, then pulls all
bookmarks, downloads image media to library/media/, and merges items
into library/items.json. Re-running only adds new bookmarks.
"""

import base64
import hashlib
import http.server
import json
import os
import re
import secrets
import subprocess
import sys
import threading
import time
import urllib.parse
import urllib.request
import webbrowser
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
MEDIA = LIB / "media"
ITEMS = LIB / "items.json"
TOKENS = LIB / ".tokens.json"

CLIENT_ID = os.environ.get("X_CLIENT_ID", "")
REDIRECT = "http://127.0.0.1:8765/callback"
SCOPES = "tweet.read users.read bookmark.read offline.access"
AUTH_URL = "https://x.com/i/oauth2/authorize"
TOKEN_URL = "https://api.x.com/2/oauth2/token"
API = "https://api.x.com/2"


def die(msg):
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(1)


# ---------- OAuth 2.0 PKCE ----------

def get_tokens():
    """Return a valid access token, refreshing or re-authorizing as needed."""
    if TOKENS.exists():
        tok = json.loads(TOKENS.read_text())
        if time.time() < tok.get("expires_at", 0) - 60:
            return tok["access_token"]
        if tok.get("refresh_token"):
            try:
                return refresh(tok["refresh_token"])
            except Exception as e:
                print(f"refresh failed ({e}), re-authorizing...")
    return authorize()


def save_tokens(data):
    data["expires_at"] = time.time() + data.get("expires_in", 7200)
    TOKENS.write_text(json.dumps(data))
    try:
        os.chmod(TOKENS, 0o600)
    except OSError:
        pass
    return data["access_token"]


def token_request(params):
    body = urllib.parse.urlencode(params).encode()
    req = urllib.request.Request(
        TOKEN_URL, data=body,
        headers={"Content-Type": "application/x-www-form-urlencoded"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())


def refresh(refresh_token):
    data = token_request({
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": CLIENT_ID,
    })
    return save_tokens(data)


def authorize():
    if not CLIENT_ID:
        die("set X_CLIENT_ID env var (see header of this file for setup)")

    verifier = base64.urlsafe_b64encode(secrets.token_bytes(48)).decode().rstrip("=")
    challenge = base64.urlsafe_b64encode(
        hashlib.sha256(verifier.encode()).digest()).decode().rstrip("=")
    state = secrets.token_urlsafe(16)

    url = AUTH_URL + "?" + urllib.parse.urlencode({
        "response_type": "code",
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT,
        "scope": SCOPES,
        "state": state,
        "code_challenge": challenge,
        "code_challenge_method": "S256",
    })

    code_holder = {}

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            q = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            if q.get("state", [""])[0] != state:
                self.send_error(400, "state mismatch")
                return
            code_holder["code"] = q.get("code", [""])[0]
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(b"<h2>Authorized. You can close this tab.</h2>")

        def log_message(self, *a):
            pass

    server = http.server.HTTPServer(("127.0.0.1", 8765), Handler)
    threading.Thread(target=server.handle_request, daemon=True).start()

    print("Opening browser for authorization...")
    webbrowser.open(url)
    print(f"If it didn't open, visit:\n{url}\n")

    while "code" not in code_holder:
        time.sleep(0.3)
    server.server_close()

    data = token_request({
        "grant_type": "authorization_code",
        "code": code_holder["code"],
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT,
        "code_verifier": verifier,
    })
    return save_tokens(data)


# ---------- API helpers ----------

def api_get(token, path, params):
    url = f"{API}{path}?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
    for attempt in range(5):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            if e.code == 429:
                wait = int(e.headers.get("x-rate-limit-reset", 0)) - time.time()
                wait = max(min(wait, 900), 15)
                print(f"rate limited, waiting {int(wait)}s...")
                time.sleep(wait)
                continue
            raise
    die("too many rate-limit retries")


# Ceiling on video bitrate when choosing which encode to pull. X publishes
# several per clip; the top one is source resolution and roughly 3x the bytes
# for no visible gain in a 240px grid tile. Override with LT_MAX_BITRATE
# (bits/sec) — set it to 0 to always take the highest quality available.
MAX_BITRATE = int(os.environ.get("LT_MAX_BITRATE", 1_200_000))


def best_variant(m):
    """A reasonably-sized mp4 for a video / animated_gif, or None for photos.

    X returns no `url` for motion media — only a `preview_image_url` poster.
    The playable files live in `variants`, which we request explicitly.
    """
    if m.get("type") not in ("video", "animated_gif"):
        return None
    mp4s = [v for v in (m.get("variants") or [])
            if v.get("content_type") == "video/mp4" and v.get("url")]
    if not mp4s:
        return None
    mp4s.sort(key=lambda v: v.get("bit_rate", 0))
    if not MAX_BITRATE:
        return mp4s[-1]["url"]
    # Best encode at or under the cap. If every variant is over it (short
    # high-motion clips sometimes are), the smallest is closest to intent.
    under = [v for v in mp4s if v.get("bit_rate", 0) <= MAX_BITRATE]
    return (under[-1] if under else mp4s[0])["url"]


def download(url, dest):
    # A zero-byte file means a previous attempt died mid-write. Treat it as
    # absent, or it is silently accepted as complete forever after.
    if dest.exists() and dest.stat().st_size > 0:
        return True
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=60) as r, open(dest, "wb") as f:
            f.write(r.read())
        return True
    except Exception as e:
        print(f"  failed to download {url}: {e}")
        return False


# ---------- Import ----------

def main():
    LIB.mkdir(exist_ok=True)
    MEDIA.mkdir(exist_ok=True)
    token = get_tokens()

    me = api_get(token, "/users/me", {})["data"]
    print(f"Authorized as @{me['username']}")

    existing = {}
    if ITEMS.exists():
        existing = {it["id"]: it for it in json.loads(ITEMS.read_text())}
    print(f"{len(existing)} items already in library")

    new_items = []
    backfilled = [0]
    pagination = None
    page = 0
    while True:
        page += 1
        params = {
            "max_results": 100,
            "expansions": "attachments.media_keys,author_id",
            "media.fields": "media_key,type,url,preview_image_url,width,height,alt_text,variants",
            "tweet.fields": "created_at,text,entities",
            "user.fields": "username,name",
        }
        if pagination:
            params["pagination_token"] = pagination
        resp = api_get(token, f"/users/{me['id']}/bookmarks", params)

        tweets = resp.get("data", [])
        media_by_key = {m["media_key"]: m
                        for m in resp.get("includes", {}).get("media", [])}
        users_by_id = {u["id"]: u
                       for u in resp.get("includes", {}).get("users", [])}
        print(f"page {page}: {len(tweets)} bookmarks")

        for t in tweets:
            author = users_by_id.get(t.get("author_id"), {})
            keys = t.get("attachments", {}).get("media_keys", [])
            for i, k in enumerate(keys):
                m = media_by_key.get(k)
                if not m:
                    continue
                img_url = m.get("url") or m.get("preview_image_url")
                if not img_url:
                    continue
                item_id = f"x_{t['id']}_{i}"
                vid_url = best_variant(m)

                # Already imported. Backfill the playable file if this is motion
                # media that predates video support — mutating `prior` in place
                # keeps its scan results, tags and notes intact.
                prior = existing.get(item_id)
                if prior:
                    if vid_url and not prior.get("video"):
                        vname = item_id + ".mp4"
                        print(f"  + video {vname}")
                        if download(vid_url, MEDIA / vname):
                            prior["video"] = f"media/{vname}"
                            backfilled[0] += 1
                    continue

                ext = os.path.splitext(urllib.parse.urlparse(img_url).path)[1] or ".jpg"
                fname = item_id + ext
                print(f"  {fname}")
                if not download(img_url, MEDIA / fname):
                    continue
                # Poster always downloads: scan.py needs a still, and it doubles
                # as the <video poster> so the grid paints before playback.
                video_rel = None
                if vid_url:
                    vname = item_id + ".mp4"
                    if download(vid_url, MEDIA / vname):
                        video_rel = f"media/{vname}"
                clean_text = re.sub(r"https://t\.co/\S+", "", t.get("text", "")).strip()
                new_items.append({
                    "id": item_id,
                    "file": f"media/{fname}",
                    "video": video_rel,
                    "source": "x",
                    "url": f"https://x.com/{author.get('username','i')}/status/{t['id']}",
                    "author": author.get("username", ""),
                    "text": clean_text,
                    "alt_text": m.get("alt_text", ""),
                    "media_type": m["type"],
                    "saved_at": t.get("created_at", ""),
                    "imported_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    "tags": [],
                    "note": "",
                    "scan": None,
                })

        pagination = resp.get("meta", {}).get("next_token")
        if not pagination:
            break

    merged = merge_items(ITEMS, new_items,
                         videos={key: item.get("video") for key, item in existing.items()})
    print(f"\nDone. {len(new_items)} new items, {len(merged)} total.")
    if backfilled[0]:
        print(f"Backfilled video for {backfilled[0]} existing items.")
    if new_items:
        print("Next: run  python3 scan.py  to make them searchable.")


if __name__ == "__main__":
    main()
