# Egg changelog

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
