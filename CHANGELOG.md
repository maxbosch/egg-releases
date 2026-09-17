# Egg changelog

## 0.1.9 — 2026-09-17

Opening a piece zooms into it, the app is drawn in its own icon set, and
typing in search stopped costing a third of a second a keystroke.

- The lightbox is the piece. A tile zooms up from where it sits on the board
  instead of cutting to a dialog, the board blurs behind it rather than going
  dark, and the piece sits on it with no card, border or grey plate around it.
  Everything the scan knows moved into a floating glass rail on the right —
  description, style, subjects, colours, extracted text — grouped into cards,
  with style and subjects as chips and colours as swatches rather than names.
- Every icon in the app is Egg's own. The UI is drawn in the Bubbles set
  rather than SF Symbols, across the library, the shelf and the menu bar, and
  the type is SF Pro Rounded throughout.
- Search keeps up with typing. A keystroke cost about 330ms of work on a
  library this size and now costs around 20ms. Thumbnails stopped thrashing
  their cache too, which is what kept filling the grid with grey cards when
  the pictures were on disk all along.
- Prototypes capture what runs. A card shows the thing itself rather than a
  stale snapshot, it opens in a window of its own, and variants stop piling
  up in the feed. Asking for a change is a floating prompt over the live page.
- The sidebar makes fewer claims. Hidden moved to View › Hidden Items, Themes
  is gone, and hearted reads as Taste. Facet pills are filled and have hover
  and press states, and a section header toggles from anywhere in its row.
- Empty states fill the canvas instead of collapsing the stack they share
  with the search bar, which had been sending it into the middle of the
  window whenever a search stopped matching.

## 0.1.8 — 2026-09-15

The library looks like your work now, and takes a drop from anywhere.

- Drag and drop into the library works. It only ever worked on an empty
  library — with anything in it the grid had no drop target, so dropping a
  file onto your own collection did nothing. Holding something over the
  window now blurs the grid and previews what you are carrying, stacked
  with a count when there are several.
- The grid is a wall of work: tiles keep their own proportions instead of
  being letterboxed into one shape on a grey plate, and artwork fills its
  tile edge to edge. Title and author are gone from under each piece (the
  lightbox carries them) — what is left is the work, a glyph when something
  isn't an image, and select and heart on hover.
- The selection bar's icons are visible again. White glyphs on clear glass
  vanished wherever a pale thumbnail sat behind the bar; the library's glass
  now carries the same wash the shelf's has.
- The window resizes properly. The grid decided its own width from its own
  contents, which slid tiles under the sidebar and pulled the floating
  search bar out of position.

## 0.1.7 — 2026-09-15

The setup release: one checklist, and scanning that doesn't need a terminal.

- Set Up Egg: a checklist of everything Egg can use — API key, coding
  agent, phone capture, sandboxes, scanning, X — showing what works and
  what one more step would unlock. Nothing blocks the app; skipping a row
  is a supported answer. In the menu-bar egg, the app menu, and the empty
  library.
- Scanning runs in the app: "Scan Library…" in the sidebar uses the key
  already in your Keychain. No terminal, no python3, no second paste of
  the key. Re-running only picks up what's new; scan.py is unchanged for
  agents.
- Full Disk Access is noticed the moment you grant it — the checklist
  offers the relaunch instead of leaving you to guess.
- X bookmarks import in the app: paste your X app's Client ID once,
  connect in the browser, then import. Shares the token file and client id
  with fetch_bookmarks.py, so app and script are interchangeable.
  Experimental: with no X app at all, the same window can read your
  bookmarks page directly — no client id, no API quota.
- Egg Mode (⌃⌥⌘E): the menu bar hides behind a wallpaper-matched cover
  with only the egg at top right, and keystrokes echo in a keycap at
  bottom left. For demos and recordings.
- Egg --doctor prints your setup as JSON and exits 0 when nothing is left
  to do, so a coding agent can configure Egg and verify its own work.
  SETUP.md is the contract; the checklist can hand it to your agent.
- Shelf: the empty state is just the egg mark, the panel is glass at rest
  and solid while focused, and the Active pill is a bolt that turns green
  when something is running.

## 0.1.6 — 2026-09-11

The tester release: Egg now assumes nothing about your setup.

- A new app icon, in every size macOS asks for.
- Sandboxes are opt-in: a fresh Egg keeps everything on your Mac —
  capture, shelf, library, feed — and sends are a local echo. Turn
  sandboxes on in Settings when you have a heyvm daemon or heyo key of
  your own. Existing setups: flip the new "Enable sandboxes" toggle once.
- The menu-bar egg always comes back at launch, even if it was once
  dragged off the menu bar.
- The shelf reads on any desktop: dark mode gets a dark wash behind the
  glass so white text survives bright backgrounds; light mode's buttons
  sit in grey containers with quieter icons.
- The shelf hugs a small pile — one or two cards no longer float in a
  fixed-height area.
- The item-count pill lives on the left beside the plus.

## 0.1.5 — 2026-09-11

The glass release.

- The shelf moves again: dragging its header, background, or any edge works
  everywhere — clicks no longer fall through the glass.
- Purely visual cards in the pile; names and details live in the rows.
- The Active band: live sandboxes with uptime, this Mac's dev servers
  (open, quit, or take one into a sandbox), and idle prototypes one click
  from booting.
- The library window wears the glass: transparent window, floating native
  toolbar, content scrolling beneath; menus across the app picked up icons.
- Empty categories are drop targets again, the selection bar speaks in
  Music-style icons, and a pass of small paddings, truncations, and hover
  states.

## 0.1.0 — 2026-09-10

First alpha. Signed, notarized, auto-updating.

- Library window and menu-bar capture in one app: search (⌘F), filters,
  themes, ideas from a selection, hearts.
- Taste skill built in: heart the pieces you'd defend, distill them into
  a skill your coding agent follows.
- Importers run by your own agent: any folder of images, X bookmarks
  (via your own X app), or anything that writes valid items — see
  ALPHA.md and skills/egg-ingest.
- Bring your own Anthropic API key; stored in your Keychain.
