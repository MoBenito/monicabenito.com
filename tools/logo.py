"""Generates the logo: wordmark with two spins (ó up, Benito's o down) and the MB spin-ball favicon.

    python tools/logo.py

Writes layouts/partials/logo.html (inline SVG; letters and arrows use currentColor, so they follow dark mode)
and static/favicon.svg, favicon-32.png, apple-touch-icon.png, icon-512.png.
Needs fontTools and rsvg-convert. The font (Outfit, SIL Open Font License) is downloaded on first use.
"""

import math
import subprocess
import urllib.request
from pathlib import Path

from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont

ROOT = Path(__file__).resolve().parent.parent
FONT_FILE = ROOT / "tools" / "fonts" / "Outfit.ttf"
FONT_URL = "https://github.com/google/fonts/raw/main/ofl/outfit/Outfit%5Bwght%5D.ttf"
WEIGHT = 500
TEAL, TEAL_D, TEAL_L, ARROW_ON_ICON = "#0f7a63", "#0a5646", "#5fc9ad", "#0b2e27"


def load_font():
    if not FONT_FILE.exists():
        FONT_FILE.parent.mkdir(parents=True, exist_ok=True)
        urllib.request.urlretrieve(FONT_URL, FONT_FILE)
    return instantiateVariableFont(TTFont(FONT_FILE), {"wght": WEIGHT})


FONT = load_font()
GS, CMAP, HMTX = FONT.getGlyphSet(), FONT.getBestCmap(), FONT["hmtx"]
UPM = FONT["head"].unitsPerEm


def glyph(ch, x, baseline, size):
    pen = SVGPathPen(GS)
    s = size / UPM
    GS[CMAP[ord(ch)]].draw(TransformPen(pen, (s, 0, 0, -s, x, baseline)))
    return pen.getCommands()


def advance(ch, size):
    return HMTX[CMAP[ord(ch)]][0] * size / UPM


def gradient(uid):
    return (f'<radialGradient id="{uid}" cx="35%" cy="30%" r="75%"><stop offset="0" stop-color="{TEAL_L}"/>'
            f'<stop offset=".55" stop-color="{TEAL}"/><stop offset="1" stop-color="{TEAL_D}"/></radialGradient>')


def arrow(cx, cy, r, tilt, tail, tip, width, head, half_width, color):
    """Arrow along a line through (cx, cy), tilted `tilt` degrees clockwise from straight up.
    tail and tip are distances from the centre in units of r; head and half_width are absolute."""
    t = math.radians(tilt)
    ux, uy = math.sin(t), -math.cos(t)
    px, py = -uy, ux
    x0, y0 = cx - ux * tail * r, cy - uy * tail * r
    xb, yb = cx + ux * (tip * r - head), cy + uy * (tip * r - head)
    xt, yt = cx + ux * tip * r, cy + uy * tip * r
    return (f'<line x1="{x0:.1f}" y1="{y0:.1f}" x2="{xb:.1f}" y2="{yb:.1f}" stroke="{color}" '
            f'stroke-width="{width:.1f}" stroke-linecap="round"/>'
            f'<polygon fill="{color}" points="{xt:.1f},{yt:.1f} {xb + px * half_width:.1f},{yb + py * half_width:.1f} '
            f'{xb - px * half_width:.1f},{yb - py * half_width:.1f}"/>')


def sphere(cx, cy, r, uid, equator_opacity=0.45, outline=None):
    """Shaded ball with an equator; `outline` adds a thin rim in that colour (currentColor = letter colour)."""
    rim = (f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{0.95 * r:.1f}" fill="none" stroke="{outline}" '
           f'stroke-width="{0.1 * r:.1f}"/>') if outline else ""
    return (f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}" fill="url(#{uid})"/>'
            f'<ellipse cx="{cx:.1f}" cy="{cy:.1f}" rx="{r:.1f}" ry="{0.3 * r:.1f}" fill="none" stroke="#fff" '
            f'stroke-opacity="{equator_opacity}" stroke-width="{0.05 * r:.1f}"/>' + rim)


def wordmark(size=100, pad=14):
    bp = BoundsPen(GS)
    GS[CMAP[ord("o")]].draw(bp)
    xmin, ymin, xmax, ymax = [v * size / UPM for v in bp.bounds]
    r = (ymax - ymin) / 2 * 1.04
    baseline = pad + 0.95 * size
    x, letters, defs, spins = pad, [], [], []
    for ch in "Mónica Benito":
        if ch in "óo":
            uid = "logo-up" if ch == "ó" else "logo-down"
            cx, cy = x + (xmin + xmax) / 2, baseline - (ymin + ymax) / 2
            defs.append(gradient(uid))
            # the arrow sits in its own group so CSS can flip it around the sphere's centre
            spins.append(sphere(cx, cy, r, uid, outline="currentColor") + f'<g class="spin-arrow" style="transform-origin:{cx:.1f}px {cy:.1f}px">'
                         + arrow(cx, cy, r, 30 if ch == "ó" else 210, 1.3, 1.7, 0.15 * r, 0.55 * r, 0.32 * r,
                                 "currentColor") + "</g>")
        elif ch != " ":
            letters.append(glyph(ch, x, baseline, size))
        x += advance("o" if ch == "ó" else ch, size)
    w, h = x + pad + 0.3 * r, baseline + 0.32 * size
    return (f'<svg xmlns="http://www.w3.org/2000/svg" class="logo" viewBox="0 0 {w:.0f} {h:.0f}" role="img" '
            f'aria-label="Mónica Benito"><defs>{"".join(defs)}</defs>'
            f'<path fill="currentColor" d="{" ".join(letters)}"/>{"".join(spins)}</svg>\n')


def favicon():
    """Spin ball with a white MB inside; the arrow passes behind the letters."""
    cx, cy, r, size = 236, 276, 200, 190
    t = math.radians(30)
    ux, uy = math.sin(t), -math.cos(t)
    width = 26
    back = arrow(cx, cy, r, 30, 1.2, 1.22, width, 0.3 * r, 0.17 * r, ARROW_ON_ICON)
    mb_w = advance("M", size) + advance("B", size)
    x0, baseline = cx - mb_w / 2, cy + 0.35 * size
    letters = glyph("M", x0, baseline, size) + glyph("B", x0 + advance("M", size), baseline, size)
    front = "".join(  # the arrow's visible pieces in front of the sphere, near its rim
        f'<line x1="{cx + ux * a * r:.1f}" y1="{cy + uy * a * r:.1f}" x2="{cx + ux * b * r:.1f}" '
        f'y2="{cy + uy * b * r:.1f}" stroke="{ARROW_ON_ICON}" stroke-width="{width}"/>'
        for a, b in ((0.62, 1.0), (-1.0, -0.75)))
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512"><defs>{gradient("f")}</defs>'
            f'{back}{sphere(cx, cy, r, "f", 0.3)}<path fill="#fff" d="{letters}"/>{front}</svg>\n')


if __name__ == "__main__":
    (ROOT / "layouts" / "partials" / "logo.html").write_text(wordmark())
    icon = ROOT / "static" / "favicon.svg"
    icon.write_text(favicon())
    for px, name in ((32, "favicon-32.png"), (180, "apple-touch-icon.png"), (512, "icon-512.png")):
        subprocess.run(["rsvg-convert", "-w", str(px), "-h", str(px), "-o", str(ROOT / "static" / name), str(icon)],
                       check=True)
    print("logo written")
