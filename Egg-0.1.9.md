# Egg 0.1.9

Opening a piece zooms into it, the app is drawn in its own icon set, and
typing in search stopped costing a third of a second a keystroke.

- **The lightbox is the piece.** Clicking a tile zooms it up from where it
  sits on the board instead of cutting to a dialog. The board blurs behind
  it rather than going dark, so the wall of work is still there as context,
  and the piece itself sits on it with no card, no border and no grey plate
  around it. Everything the scan knows moved into a floating glass rail on
  the right — description, style, subjects, colours and extracted text,
  grouped into cards, with style and subjects as chips and colours as actual
  swatches instead of a list of names. `ⓘ` slides the rail in and out from
  the right edge; the controls stay put either way.
- **Every icon in the app is Egg's own.** The UI is drawn in the Bubbles
  set rather than SF Symbols — 131 places across the library, the shelf and
  the menu bar — and the type is SF Pro Rounded throughout, including the
  sidebar, which had been asking for it and not getting it.
- **Search keeps up with typing.** A keystroke used to cost about 330ms of
  work on a library this size, which is what made the field feel like it was
  catching up with you. It is now around 20ms at an ordinary typing pace.
  Thumbnails stopped thrashing their cache too — the grid was re-decoding
  every tile that scrolled, which is why it kept filling with grey cards
  when the pictures were on disk all along.
- **Prototypes capture what runs.** A prototype's card shows the thing
  itself rather than a stale snapshot, it opens in a window of its own, and
  variants stop piling up in the feed. Asking for a change is a floating
  prompt over the live page instead of a strip bolted under it.
- **The sidebar makes fewer claims.** Hidden moved to View › Hidden Items,
  Themes is gone — Refine and the header count already said it — and
  hearted reads as Taste. Facet pills are filled, with hover and press
  states, and a section header toggles from anywhere in its row rather than
  from the chevron alone.
- **Empty states fill the canvas.** They were sizing to their own content,
  which collapsed the stack they share with the floating search bar and sent
  it into the middle of the window whenever a search stopped matching. A
  search that finds nothing now keeps a blurred ghost of the last results
  behind it.
