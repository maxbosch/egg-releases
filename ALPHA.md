# Egg — alpha

Egg is a local-first library for the visual things you save. Everything you
put in it is scanned once by Claude into a searchable record — description,
style, subjects, colors, text — and the pieces you heart can be distilled
into a taste skill your coding agents follow. It's your data, in a folder,
on your Mac.

## Install

1. Download: https://feedegg.com/
2. Drag Egg to Applications.
3. Egg → Settings → paste your Anthropic API key
   (console.anthropic.com → API keys). It's stored in your Keychain.

### First launch (this build is unsigned — one extra step)

The alpha build isn't notarized yet, so macOS will refuse to open it the
first time ("Egg is damaged" or "cannot be opened"). Either path works:

- Try to open Egg once, then go to **System Settings → Privacy & Security**,
  scroll down, and click **Open Anyway** next to the Egg message. Open Egg
  again and confirm.
- Or, in Terminal:

  ```bash
  xattr -d com.apple.quarantine /Applications/Egg.app
  ```

  then open Egg normally.

This is once per install. Updates this week are "download the new DMG and
replace the app" — auto-update arrives with the signed build.

## Capture and browse in one app

Egg includes both the library window and the menu-bar capture panel. Use the egg
icon to open the shelf, capture a screenshot, or record your screen (macOS 15+).
Captures appear in the library within a few seconds. Closing the library window
keeps capture running; choose **Open Egg** from the menu bar to return to it.
Choose **Quit Egg** when you want to stop both.

If you used the separate menu-bar app, quit it before opening this build. Your
existing captures and capture preferences carry over. macOS may ask you to grant
capture permissions again. Set your API key once in **Settings → Library**;
shortcuts, gestures, Messages, and backend settings are in **Settings → Capture**.
Run the scanner separately to describe and index captures.

## Get your stuff in

The library starts empty — everything in it will be yours. The fastest
first fill is a folder you already have (screenshots, saved images, a
moodboard). Paste this into Claude Code (or Cursor) in an empty folder:

> Clone https://github.com/maxbosch/egg-releases.git, read
> `skills/egg-ingest/SKILL.md` in it, then: import my folder
> `~/Desktop/inspo` (any folder of images works), and when it finishes
> run the scan with my ANTHROPIC_API_KEY. Tell me before anything that
> costs money.

The scan takes a few minutes and costs roughly a cent per hundred images.
Re-running either step only picks up what's new.

## X bookmarks (optional)

The import runs against your own X developer app — your credentials, your
Mac, nothing routed through or billed to anyone else. One-time setup,
about three minutes:

1. Create an app at https://console.x.com (free).
2. In the app's auth settings, enable OAuth 2.0 with type **Native App**
   (public client), callback URL `http://127.0.0.1:8765/callback`, and
   scopes `tweet.read users.read bookmark.read offline.access`.
3. Copy the Client ID.

Then tell your agent:

> Run the X bookmarks import with my client id `<yours>`, and when it
> finishes scan what's new.

A browser window opens once for you to authorize; tokens are stored on
your Mac and refreshed locally.

## What to try

- **Search** (the floating bottom search bar, or ⌘F) — it matches what's *in* the images: "brutalist poster",
  "warm off-white interior", an author, your own notes.
- **Filters** — media kinds, sources, and style/subject/color sections in the sidebar; **Themes**
  shows what your library keeps returning to.
- **Select a few images** with their corner checkmarks, open **Ideas**, add an optional
  focus line, and choose **Generate Ideas** —
  Claude reads the selection as a moodboard and writes idea directions.
- **Heart** the pieces you'd defend. Then have your agent run
  `scripts/make_skill.py` — you get a skill that makes your agent design
  like you. That loop is the whole product.
- Point your agent at `skills/egg-ingest/SKILL.md` and ask it to import
  anything else — a folder of screenshots, are.na, a URL list. The library
  is just files; anything that writes valid items is an importer.

## The one question

What did you want to put into Egg that you couldn't? Tell us in the group
thread — that answer decides what gets built next.
