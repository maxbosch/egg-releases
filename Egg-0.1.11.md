# Egg 0.1.11

The shelf stops following your desktop's appearance and supplies its own, the
app has a colour that isn't borrowed from System Settings, and the sidebar
toggle can be clicked again.

- **The shelf is a HUD.** It spent its life drawing the wrong state: a
  material tints toward the appearance it renders in and changes with the
  window's active state, and a floating panel is unfocused most of the time —
  so the system drew the panel's heaviest look exactly where the design wanted
  its lightest, and in light mode it lightened until the panel landed at white
  over a white window. Nothing on it could be styled once and be right twice.
  The panel is now pinned dark in both appearances, the way Spotlight and
  Control Center are, so it darkens a white page the same way it darkens a
  wallpaper. At rest it is glass and a hairline; clicked into, a heavier
  material fades in behind the content.
- **Its controls agree with each other.** The four circles and the count pill
  were three different answers to the same question — `.borderlessButton` and
  `.plain` repaint their own labels, so a colour set inside the label was
  discarded, and only the × wore a style that honoured it. One colour now, one
  ring, one container: no fill at rest so a control is the panel showing
  through, a fill on engagement and under the pointer. Hover and press are
  drawn rather than left to the system, which mutes both on a non-activating
  panel.
- **A capture keeps your appearance.** The panel is chrome and the card is
  not: a text clip's paper and ink, and the canvas under artwork, follow the
  mode you actually chose. Artwork fills its card edge to edge now instead of
  sitting on a mat with a drop shadow — six tiles each showing a margin read
  as six pictures of cards rather than six cards.
- **Egg's accent is Egg's.** `AccentColor` was an empty colorset the project
  never named, so the accent resolved to whatever you had picked in System
  Settings. It is the brand yellow, with a near-black ink for anything drawn
  on top of it — at that luminance it cannot carry white, which the borrowed
  blue could.
- **The sidebar toggle works.** As a floating overlay it rendered perfectly
  and was dead to the pointer: the window draws content under the title bar,
  but AppKit's title bar takes the clicks, so only the sliver dipping below
  the inset could be hit. It is a toolbar item again, aligned and dressed by
  the thing that handles every other control up there. The lightbox's rail
  toggle is mirrored, since it opens on the other side of the window.
- **The library window has a floor.** Its minimum size was never asked for —
  the scene declared no resizability — so the split view compressed the
  sidebar past its own minimum until the row labels truncated to "E…" and
  "V…". The floor is the sidebar's and the grid's added together. Open in
  Window joined the toolbar, the search and selection bars became one capsule
  instead of two near-identical ones, and the Taste row is filled like every
  other glyph beside it.
- **A restored shelf opens at the right height.** The capture area took its
  size from a change notification, which does not fire for captures that were
  already there — so a remembered clip drew its full-size card into an
  empty-shelf slot and sat on the chrome above and below it.
