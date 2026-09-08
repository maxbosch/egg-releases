# Coop — alpha

Coop is a local-first library for the visual things you save. Everything you
put in it is scanned once by Claude into a searchable record — description,
style, subjects, colors, text — and the pieces you heart can be distilled
into a taste skill your coding agents follow. It's your data, in a folder,
on your Mac.

## Install

1. Download: https://maxbosch.github.io/coop-releases/
2. Drag Coop to Applications.
3. Coop → Settings → paste your Anthropic API key
   (console.anthropic.com → API keys). It's stored in your Keychain.

### First launch (this build is unsigned — one extra step)

The alpha build isn't notarized yet, so macOS will refuse to open it the
first time ("Coop is damaged" or "cannot be opened"). Either path works:

- Try to open Coop once, then go to **System Settings → Privacy & Security**,
  scroll down, and click **Open Anyway** next to the Coop message. Open Coop
  again and confirm.
- Or, in Terminal:

  ```bash
  xattr -d com.apple.quarantine /Applications/Coop.app
  ```

  then open Coop normally.

This is once per install. Updates this week are "download the new DMG and
replace the app" — auto-update arrives with the signed build.

## Get your X bookmarks in

Paste this into Claude Code (or Cursor) in an empty folder:

> Clone https://github.com/maxbosch/coop-releases.git, read
> `skills/coop-ingest/SKILL.md` in it, then: run the X bookmarks import
> with client id `<X_CLIENT_ID>`, and when it finishes run the scan with
> my ANTHROPIC_API_KEY. Tell me before anything that costs money.

A browser window will open once for X authorization. The scan takes a few
minutes and costs roughly a cent per hundred images. Re-running either step
only picks up what's new.

## What to try

- **Search** (`/`) — it matches what's *in* the images: "brutalist poster",
  "warm off-white interior", an author, your own notes.
- **Filters** — style, subject, and color chips in the left rail; **Themes**
  shows what your library keeps returning to.
- **Select a few images** (click), add an optional focus line, hit **G** —
  Claude reads the selection as a moodboard and writes idea directions.
- **Heart** the pieces you'd defend. Then have your agent run
  `scripts/make_skill.py` — you get a skill that makes your agent design
  like you. That loop is the whole product.
- Point your agent at `skills/coop-ingest/SKILL.md` and ask it to import
  anything else — a folder of screenshots, are.na, a URL list. The library
  is just files; anything that writes valid items is an importer.

## The one question

What did you want to put into Coop that you couldn't? Tell us in the group
thread — that answer decides what gets built next.
