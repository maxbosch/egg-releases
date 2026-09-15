# Egg 0.1.8

The library looks like your work now, and takes a drop from anywhere.

- **Drag and drop into the library works.** It only ever worked on an empty
  library: with anything in it, the grid had no drop target at all, so
  dropping a file onto your own collection did nothing. Any state takes a
  drop now — and while something is held over the window the grid steps back
  behind a blur and what you are carrying is previewed in the middle, stacked
  with a count when there are several.
- **The grid is a wall of work.** Tiles keep their own proportions in a
  column layout instead of being letterboxed into one shape on a grey plate,
  and artwork fills its tile edge to edge. The title and author are gone from
  under each piece — the lightbox already carries them — leaving the work,
  a small glyph when something isn't an image, and the select and heart
  controls on hover.
- **The selection bar's icons are visible again.** Heart, collection and hide
  are white glyphs, and the bar floats over your grid: crossing a pale
  screenshot they were white on white and simply disappeared. The library's
  glass now carries the same wash the shelf's has, for the same reason.
- **The window resizes properly.** The grid was deciding its own width from
  its own contents, which let tiles slide under the sidebar and pulled the
  floating search bar out of position as you resized.
