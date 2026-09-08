/* Harvest every bookmark ID from x.com/i/bookmarks.
 *
 * Read this before running it — it is deliberately short so you can.
 * It does three things and nothing else:
 *   1. reads post IDs out of the page you already have open
 *   2. scrolls down to load more
 *   3. saves the IDs to a file on your Mac
 * No network calls, no credentials touched, nothing sent anywhere.
 *
 * HOW TO RUN
 *   1. Open  https://x.com/i/bookmarks  and log in
 *   2. Cmd+Option+J (Chrome) or Cmd+Option+C (Safari, after enabling
 *      Develop menu) to open the console
 *   3. Paste this whole file, press Enter, then leave the tab in the
 *      foreground and don't touch it — background tabs stop scrolling
 *   4. It prints a running count. When it finishes it downloads
 *      bookmark-ids.json to your Downloads folder
 */
(async () => {
  const ids = new Set();

  // Each rendered post is one <article>. Its canonical permalink is the
  // only link inside that also wraps a <time> element — this avoids
  // picking up quoted posts, replies and "show this thread" links.
  const collect = () => {
    document.querySelectorAll('article').forEach(art => {
      const link = [...art.querySelectorAll('a[href*="/status/"]')]
        .find(a => a.querySelector('time'));
      if (!link) return;
      const m = link.getAttribute('href').match(/\/status\/(\d+)/);
      if (m) ids.add(m[1]);
    });
  };

  // X virtualises the list: rows are destroyed once scrolled past, so we
  // must collect on every step rather than once at the end.
  let stableRounds = 0, lastCount = 0, lastY = -1;
  collect();
  console.log('starting…');

  while (stableRounds < 6) {
    window.scrollBy(0, window.innerHeight * 0.9);
    await new Promise(r => setTimeout(r, 1000));  // let X fetch the next page
    collect();

    const y = Math.round(window.scrollY);
    // Only stop when BOTH the count and the scroll position have stopped
    // moving — count alone plateaus across stretches of already-seen posts.
    if (ids.size === lastCount && y === lastY) stableRounds++;
    else stableRounds = 0;
    lastCount = ids.size;
    lastY = y;
    console.log(`collected ${ids.size} bookmarks…`);
  }

  const blob = new Blob([JSON.stringify([...ids], null, 1)],
                        {type: 'application/json'});
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = 'bookmark-ids.json';
  a.click();
  console.log(`DONE — ${ids.size} bookmark IDs saved to bookmark-ids.json`);
})();
