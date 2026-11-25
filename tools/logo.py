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


def favicon(background=None, width=330, tip_radius=300):
    """A bold white MB, centred in a full-size spin ball; the M's right diagonal shoots out as the spin arrow,
    its tip leaving the ball towards the top right corner (outside the ball it is teal, so it shows on light
    and dark tab bars). Made to stay readable at 16 px in a browser tab: no equator (too fine to see), and a
    darker highlight than the logo so the M keeps its contrast. `width` is the letters' span in px, `tip_radius`
    the arrow tip's distance from the centre (the ball's radius is 256). `background` fills the square behind
    the ball and shrinks the picture a little (for app icons, which iOS shows on black and with round corners)."""
    bold = instantiateVariableFont(TTFont(FONT_FILE), {"wght": 700})
    gs, cmap = bold.getGlyphSet(), bold.getBestCmap()
    bounds = {}
    for ch in "MB":
        bp = BoundsPen(gs)
        gs[cmap[ord(ch)]].draw(bp)
        bounds[ch] = bp.bounds
    gap = 0.04 * bold["head"].unitsPerEm
    s = width / ((bounds["M"][2] - bounds["M"][0]) + gap + (bounds["B"][2] - bounds["B"][0]))
    left, baseline = 256 - width / 2, 256 + bounds["M"][3] * s / 2  # centred on the cap height
    pen = SVGPathPen(gs)
    x = left
    for ch in "MB":
        gs[cmap[ord(ch)]].draw(TransformPen(pen, (s, 0, 0, -s, x - bounds[ch][0] * s, baseline)))
        x += (bounds[ch][2] - bounds[ch][0] + gap) * s
    # The arrow continues the M's right diagonal past its top corner. In Outfit Bold (font units) that stroke
    # lies between the line (400.5, 272.5)-(678, 706) and the parallel line through (481, 152).
    (ax, ay), (bx, by), (qx, qy) = (400.5, 272.5), (678, 706), (481, 152)
    length = math.hypot(bx - ax, by - ay)
    ux, uy = (bx - ax) / length, (by - ay) / length   # along the stroke, up and to the right
    nx, ny = uy, -ux                                  # across it
    stroke = (qx - ax) * nx + (qy - ay) * ny
    cx0, cy0 = ax + nx * stroke / 2, ay + ny * stroke / 2

    def px(t, off=0.0):  # t along the stroke's centre line, off across it (font units) -> picture px
        fx, fy = cx0 + ux * t + nx * off, cy0 + uy * t + ny * off
        return left + (fx - bounds["M"][0]) * s, baseline - fy * s

    head_len, head_w = 290, 430
    lo, hi = length, length + 3000  # find the shaft length that puts the tip at tip_radius
    for _ in range(50):
        mid = (lo + hi) / 2
        tx, ty = px(mid + head_len)
        lo, hi = (mid, hi) if math.hypot(tx - 256, ty - 256) < tip_radius else (lo, mid)
    end = lo
    arrow_d = "M" + "L".join("{:.1f} {:.1f}".format(*px(t, off)) for t, off in (
        (300, -stroke / 2), (end, -stroke / 2), (end, -head_w / 2), (end + head_len, 0),
        (end, head_w / 2), (end, stroke / 2), (300, stroke / 2))) + "Z"
    shade = (f'<radialGradient id="f" cx="35%" cy="30%" r="75%"><stop offset="0" stop-color="#2a9e83"/>'
             f'<stop offset=".55" stop-color="{TEAL}"/><stop offset="1" stop-color="{TEAL_D}"/></radialGradient>'
             f'<clipPath id="ball"><circle cx="256" cy="256" r="256"/></clipPath>')
    picture = (f'<circle cx="256" cy="256" r="256" fill="url(#f)"/><path fill="{TEAL}" d="{arrow_d}"/>'
               f'<path fill="#fff" clip-path="url(#ball)" d="{pen.getCommands()}{arrow_d}"/>')
    if background:
        picture = (f'<rect width="512" height="512" fill="{background}"/>'
                   f'<g transform="translate(256 256) scale(.84) translate(-256 -256)">{picture}</g>')
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512"><defs>{shade}</defs>{picture}</svg>\n'


if __name__ == "__main__":
    (ROOT / "layouts" / "partials" / "logo.html").write_text(wordmark())
    icon = ROOT / "static" / "favicon.svg"
    icon.write_text(favicon())
    on_light = favicon(background="#fbfcfb").encode()  # home-screen icons get a square background
    for px, name, svg in ((32, "favicon-32.png", icon.read_bytes()), (180, "apple-touch-icon.png", on_light),
                          (512, "icon-512.png", on_light)):
        subprocess.run(["rsvg-convert", "-w", str(px), "-h", str(px), "-o", str(ROOT / "static" / name)],
                       input=svg, check=True)
    print("logo written")
