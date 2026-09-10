# Egg landing page

Editable source for Egg’s landing page, with the scroll-cracking egg and 18 collectible eggs in a 3D meadow.

## Open the playable preview

Open `deliverables/egg-playable.html` in a browser. This self-contained file includes the game and requires no server or network downloads. The earlier static design is preserved as `deliverables/egg-preview.html`.

## Run and edit the site

Requires Node.js 22.13 or later and npm.

```sh
npm ci
npm run dev
```

Open the local URL printed by the development server. Edit `app/page.tsx` for the landing page, `app/globals.css` for styling, and `components/egg/` for the 3D scene and collection behavior.

```sh
npm run build
```

## Saved state

The build and game-logic checks passed. The most recent private deployment status could not be confirmed because Sites returned transport errors. See `deliverables/publishing-status.txt` for the saved version and deployment details.

Early-access signup still needs a signup URL or contact email. No signup requests are collected.

The `.openai/hosting.json` file preserves the existing Site identity. Dependency caches, generated builds, and the original workspace’s Git history are excluded from this copy.
