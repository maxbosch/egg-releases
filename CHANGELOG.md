# Egg changelog

## 0.1.11 — 2026-10-07

The shelf stops following your desktop's appearance and supplies its own, the
app has a colour that isn't borrowed from System Settings, and the sidebar
toggle can be clicked again.

- The shelf is a HUD. It had been drawing the wrong state: a material tints
  toward the appearance it renders in and changes with the window's active
  state, and a floating panel is unfocused most of the time — so the system
  drew the panel's heaviest look exactly where the design wanted its lightest,
  and in light mode it lightened until the panel landed at white over a white
  window. It is pinned dark in both appearances now, the way Spotlight and
  Control Center are, so it darkens a white page the same way it darkens a
  wallpaper. At rest it is glass and a hairline; clicked into, a heavier
  material fades in behind the content.
- Its controls agree with each other. The four circles and the count pill were
  three different answers to the same question, because `.borderlessButton`
  and `.plain` repaint their own labels and discard a colour set inside one.
  One colour now, one ring, one container — no fill at rest so a control is
  the panel showing through, a fill on engagement and under the pointer. Hover
  and press are drawn rather than left to the system, which mutes both on a
  non-activating panel.
- A capture keeps your appearance. The panel is chrome and a card is not: a
  text clip's paper and ink, and the canvas under artwork, follow the mode you
  chose. Artwork fills its card edge to edge instead of sitting on a mat with
  a drop shadow.
- Egg's accent is Egg's. AccentColor was an empty colorset the project never
  named, so the accent resolved to whatever you had picked in System Settings.
  It is the brand yellow, with a near-black ink for anything drawn on top of
  it — at that luminance it cannot carry white, which the borrowed blue could.
- The sidebar toggle works. As a floating overlay it rendered perfectly and
  was dead to the pointer: the window draws content under the title bar, but
  AppKit's title bar takes the clicks. It is a toolbar item again. The
  lightbox's rail toggle is mirrored, since it opens on the other side of the
  window.
- The library window has a floor. Its minimum size was never asked for — the
  scene declared no resizability — so the split view compressed the sidebar
  past its own minimum until the row labels truncated to "E…" and "V…". Open
  in Window joined the toolbar, the search and selection bars became one
  capsule, and the Taste row is filled like every other glyph beside it.
- A restored shelf opens at the right height. The capture area took its size
  from a change notification, which does not fire for captures that were
  already there, so a remembered clip drew its full-size card into an
  empty-shelf slot and sat on the chrome above and below it.

## 0.1.10 — 2026-09-30

First run walks you through the iMessage setup instead of describing it, the
shelf's sandbox starts before you need it, and Egg Mode stops swallowing the
click on a plain desktop.

- The setup is a flow, not a paragraph. Giving Egg its own address means a
  web flow behind Apple ID auth, an emailed code and a checkbox in Messages —
  three apps and six steps, which both places that asked for the address had
  compressed into one sentence above a text field. First launch now walks it:
  grants, then the address, then a test message that proves both. It suggests
  an address derived from your own, copies it, opens appleid.apple.com and
  then Messages, and waits to see something land before calling the setup
  done. Nothing is written until the flow finishes, so abandoning it halfway
  leaves your configuration as it was.
- You can get back to it. The walkthrough was reachable only on first launch
  and from a Welcome item buried in the app menu. Settings now has Set Up
  Egg's Address… beside the field (Change Address… once set), and the
  checklist row grows a Set Up Address… button while no address exists.
- Allow Contacts asks, rather than naming a switch that isn't there. The
  Messages panel sent testers to System Settings › Privacy & Security ›
  Contacts to find an empty list — macOS lists an app there only after it has
  asked, and Egg hadn't. A button now fires the real prompt and re-reads the
  panel. The System Settings path stays for denied, where it is the only
  route left.
- The shelf's VM is warm before the first send. The Active band opens with a
  Shelf sandbox row, labelled Cloud VM or Local VM, and Start boots it up
  front so a send doesn't wait out 20–60 seconds of boot. Start, Send and the
  instant actions share one in-flight boot instead of each booting a VM and
  leaving the extras to idle out, and reconnecting to a prototype renews its
  hour so it can't be reaped mid-edit.
- The sandbox runs on Firecracker. Cloud sandboxes moved onto the
  egg-sandbox-v1 image with Claude Code and Node 22 baked in, so a boot
  spends no time downloading them, and commands carry an explicit timeout.
  Local deploys wait out a full cold boot rather than timing out and dropping
  the half-booted VM.
- Egg Mode covers the bar on a plain desktop. A solid-colour desktop has no
  wallpaper file to read, and macOS can keep showing a cached picture whose
  original is gone. Either way the cover was built and never shown: the HUD
  appeared, the menu bar stayed, and the mode looked like it had ignored the
  click. The strip goes up regardless now, and says once why it is plain.

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
