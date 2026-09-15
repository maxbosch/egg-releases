# Egg 0.1.7

The setup release: one checklist, and scanning that doesn't need a terminal.

- **Set Up Egg.** A checklist of everything Egg can use — your API key, the
  coding agent, phone capture, sandboxes, scanning, X — each showing what's
  working and what one more step would unlock. Nothing blocks the app:
  skipping a row is a supported answer. Open it from the menu-bar egg, the
  app menu, or the empty library.
- **Scanning runs in the app.** "Scan Library…" in the sidebar, using the
  key already in your Keychain — no terminal, no python3, no pasting the
  key a second time. Progress as it goes, stop whenever, and re-running
  only picks up what's new. The `scan.py` path still works exactly as
  before for agents.
- **Full Disk Access tells you when it lands.** The checklist notices the
  moment you flip the toggle and offers to relaunch, instead of leaving you
  to guess whether it took.
- **X bookmarks import in the app.** Paste your X app's Client ID once and
  choose Connect — the browser handles consent, and Import pulls everything
  new. It shares the token file and client ID with `fetch_bookmarks.py`, so
  the app and the script are interchangeable. **Experimental:** if you have
  no X developer app at all, the same window can read your bookmarks page
  directly — no client ID, no API quota.
- **Egg Mode** (⌃⌥⌘E). The menu bar disappears behind a wallpaper-matched
  cover with only the egg at the top right, and keystrokes echo in a keycap
  at the bottom left. For demos and recordings; closing it is the whole
  undo.
- **For the terminal-inclined:** `Egg.app/Contents/MacOS/Egg --doctor`
  prints your setup as JSON and exits 0 when nothing is left to do — so a
  coding agent can configure Egg and check its own work. `SETUP.md` is the
  contract it follows, and the checklist has a button that hands your agent
  the whole thing.
- The shelf keeps refining: the empty state is just the egg mark, the panel
  is glass at rest and solid while focused, and the Active pill is a bolt
  that turns green when something is running.
