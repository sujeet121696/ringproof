"""Builds Ringproof's mark, logo and favicon SVGs (kharidwise palette and style).

Wordmark letters are taken as outlines from Bricolage Grotesque (OFL), the dashboard's display
font, so the logo looks identical everywhere. Everything else is drawn here by hand.
"""

import sys
from pathlib import Path

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont

OUT = Path(sys.argv[1])
FONT = Path(sys.argv[2])
OUT.mkdir(parents=True, exist_ok=True)

NAVY, BLUE, GREEN, WHITE = "#0A2540", "#0077B6", "#00C853", "#FFFFFF"

# --- Mark (64 x 64) --------------------------------------------------------------------------
SHIELD = "M30 6 51 13.5v17c0 13.5-9 23-21 28.5C18 53.5 9 44 9 30.5v-17Z"

# Our own handset, drawn as one thick stroke (receiver handle) with two rounded pads.
HANDSET = f"""
  <g fill="none" stroke="{WHITE}" stroke-linecap="round" stroke-linejoin="round">
    <path d="M20.6 23.2c-1.9 7.2 3 15.4 10.6 18.6" stroke-width="5.6"/>
  </g>
  <g fill="{WHITE}">
    <rect x="15.6" y="18.4" width="11.6" height="8.2" rx="3.6" transform="rotate(-62 21.4 22.5)"/>
    <rect x="28.2" y="37.6" width="11.6" height="8.2" rx="3.6" transform="rotate(-25 34 41.7)"/>
  </g>"""

# Green "checked" badge with rays, in the spirit of kharidwise's verified tick.
BADGE = f"""
  <circle cx="47" cy="16" r="9.2" fill="{GREEN}" stroke="{WHITE}" stroke-width="2.4"/>
  <path d="M42.6 16.2l3 3 5.8-6.2" fill="none" stroke="{WHITE}" stroke-width="2.6"
        stroke-linecap="round" stroke-linejoin="round"/>
  <g stroke="{GREEN}" stroke-width="2.2" stroke-linecap="round">
    <path d="M47 4.2V1.4"/><path d="M54.6 7.4l1.9-2.1"/><path d="M58.6 13.9l2.7-.6"/>
  </g>"""

GRADIENT = f"""<defs>
    <linearGradient id="rp-g" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="{NAVY}"/><stop offset="1" stop-color="{BLUE}"/>
    </linearGradient>
  </defs>"""


FAV_BADGE = f"""
  <circle cx="48.5" cy="14.5" r="8" fill="{GREEN}" stroke="{WHITE}" stroke-width="2.2"/>
  <path d="M44.8 14.7l2.6 2.6 5-5.4" fill="none" stroke="{WHITE}" stroke-width="2.4"
        stroke-linecap="round" stroke-linejoin="round"/>"""


def mark_body(rays: bool = True) -> str:
    badge = BADGE if rays else FAV_BADGE
    return f"""{GRADIENT}
  <path d="{SHIELD}" fill="url(#rp-g)"/>{HANDSET}{badge}"""


def write(name: str, svg: str) -> None:
    (OUT / name).write_text(svg.strip() + "\n", encoding="utf-8")


write("logo-mark.svg", f"""
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" width="64" height="64" role="img" aria-label="Ringproof">
  {mark_body()}
</svg>""")

# Favicon: no rays (they turn to noise at 16 px), badge kept.
write("favicon.svg", f"""
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" width="64" height="64">
  {mark_body(rays=False)}
</svg>""")

# --- Wordmark as outlines ---------------------------------------------------------------------
font = TTFont(FONT)
cmap, glyphs, hmtx = font.getBestCmap(), font.getGlyphSet(), font["hmtx"]
SIZE, BASELINE, X0 = 42, 46, 76  # font size in px, baseline y, start x (after the mark)
scale = SIZE / font["head"].unitsPerEm


def word(text: str, x: float) -> tuple[str, float]:
    paths = []
    for ch in text:
        name = cmap[ord(ch)]
        pen = SVGPathPen(glyphs)
        glyphs[name].draw(TransformPen(pen, (scale, 0, 0, -scale, x, BASELINE)))
        paths.append(pen.getCommands())
        x += hmtx[name][0] * scale
    return " ".join(p for p in paths if p), x


ring, x = word("Ring", X0)
proof, x = word("proof", x)
width = round(x + 4)

write("logo.svg", f"""
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} 64" width="{width}" height="64" role="img" aria-label="Ringproof">
  <style>
    .rp-ring {{ fill: {NAVY}; }}
    @media (prefers-color-scheme: dark) {{ .rp-ring {{ fill: #E6E8EB; }} }}
  </style>
  {mark_body()}
  <path class="rp-ring" d="{ring}"/>
  <path fill="{GREEN}" d="{proof}"/>
</svg>""")
print("logo width", width)
