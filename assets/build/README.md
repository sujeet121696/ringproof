# Brand build

Rebuilds the logo, favicon and app icons. Run only when the design changes; outputs are committed.

| Script | Makes | Needs |
|---|---|---|
| `make_svgs.py OUT FONT` | `logo.svg`, `logo-mark.svg`, `favicon.svg` | Python: `fonttools`, `brotli` |
| `make_pngs.mjs SRC OUT` | `apple-touch-icon.png`, `icons/icon-192/512/maskable-512.png`, `fav-16/32/48.png` | Node: `sharp` |
| `make_ico.py OUT` | `favicon.ico` (16, 32, 48) from the `fav-*.png` | Python: `pillow` |

`FONT` is `web/public/fonts/bricolage-latin.woff2`: the wordmark letters are converted to outlines
from it, so the logo looks the same everywhere. Install the tools somewhere outside the repo
(they are not app dependencies), then copy the outputs to `assets/` and `web/public/`.

All artwork is original: shield, handset, badge and rays are drawn in `make_svgs.py`. Style and
colours follow kharidwise (see `docs/DESIGN.md` §4).
