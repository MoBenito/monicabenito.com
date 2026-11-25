"""Draws the illustrations of some news posts (featured.png and featured-dark.png in their page bundles).

    python tools/newsart.py            # all
    python tools/newsart.py gemos      # only those whose folder name contains "gemos"

Same visual language as the logo: teal spin balls with an arrow, simple flat shapes. Each picture is drawn twice,
with light-mode and dark-mode line colours, on a transparent background (16:9, so the home page can crop tiles).
Needs rsvg-convert.
"""

import math
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NEWS = ROOT / "content" / "news"
W, H = 1600, 900
TEAL, TEAL_D, TEAL_L = "#0f7a63", "#0a5646", "#5fc9ad"
THEMES = {
    "light": {"ink": "#0b2e27", "soft": "#cfe3dc", "muted": "#7d8f88", "paper": "#ffffff", "accent": TEAL},
    "dark": {"ink": "#e3ece8", "soft": "#2a3833", "muted": "#7f918a", "paper": "#1d2723", "accent": "#4fd1ad"},
}


def defs():
    return (f'<radialGradient id="ball" cx="35%" cy="30%" r="75%"><stop offset="0" stop-color="{TEAL_L}"/>'
            f'<stop offset=".55" stop-color="{TEAL}"/><stop offset="1" stop-color="{TEAL_D}"/></radialGradient>')


def spin(cx, cy, r, tilt, c, arrow=True):
    """Spin ball with equator and an arrow through it, tilted `tilt` degrees clockwise from up."""
    out = (f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}" fill="url(#ball)"/>'
           f'<ellipse cx="{cx:.1f}" cy="{cy:.1f}" rx="{r:.1f}" ry="{0.3 * r:.1f}" fill="none" stroke="#fff" '
           f'stroke-opacity=".45" stroke-width="{0.05 * r:.1f}"/>')
    if not arrow:
        return out
    t = math.radians(tilt)
    ux, uy = math.sin(t), -math.cos(t)
    px, py = -uy, ux
    tail, tip, head, half = 1.35 * r, 1.75 * r, 0.5 * r, 0.3 * r
    bx, by = cx + ux * (tip - head), cy + uy * (tip - head)
    out += (f'<line x1="{cx - ux * tail:.1f}" y1="{cy - uy * tail:.1f}" x2="{bx:.1f}" y2="{by:.1f}" '
            f'stroke="{c["ink"]}" stroke-width="{0.14 * r:.1f}" stroke-linecap="round"/>'
            f'<polygon fill="{c["ink"]}" points="{cx + ux * tip:.1f},{cy + uy * tip:.1f} '
            f'{bx + px * half:.1f},{by + py * half:.1f} {bx - px * half:.1f},{by - py * half:.1f}"/>')
    return out


def wave(x0, x1, y, amp, periods, c, width=10, colour=None, phase=0.0):
    pts = []
    for i in range(241):
        x = x0 + (x1 - x0) * i / 240
        pts.append(f"{x:.1f},{y + amp * math.sin(2 * math.pi * periods * i / 240 + phase):.1f}")
    return (f'<polyline points="{" ".join(pts)}" fill="none" stroke="{colour or c["accent"]}" '
            f'stroke-width="{width}" stroke-linecap="round" stroke-linejoin="round"/>')


# --- the pictures -------------------------------------------------------------------------------------------

def emmy_noether(c):
    """Spin-based Floquet processor: a row of spins riding a periodic drive, precessing in step with it."""
    out = wave(150, 1450, 640, 70, 2.5, c, 12)
    out += wave(150, 1450, 640, 70, 2.5, c, 4, c["soft"], math.pi)
    for i, x in enumerate((380, 660, 940, 1220)):  # centred on x = 800 like the wave
        tilt = 40 * math.sin(2 * math.pi * 2.5 * (x - 150) / 1300)
        out += f'<line x1="{x}" y1="560" x2="{x}" y2="430" stroke="{c["muted"]}" stroke-width="5" stroke-dasharray="4 14" stroke-linecap="round"/>'
        out += spin(x, 330, 95, tilt, c)
    return out


def professor(c):
    """New professorship: a university building with a spin ball as its round window."""
    ink, soft = c["ink"], c["soft"]
    out = f'<polygon points="400,330 800,130 1200,330" fill="none" stroke="{ink}" stroke-width="16" stroke-linejoin="round"/>'
    out += f'<rect x="420" y="330" width="760" height="34" rx="6" fill="{ink}"/>'
    for i in range(6):  # pillars spaced evenly around the centre line x = 800
        out += f'<rect x="{800 + (i - 2.5) * 130 - 28:.0f}" y="390" width="56" height="330" rx="10" fill="{soft}"/>'
    out += f'<rect x="380" y="740" width="840" height="34" rx="6" fill="{ink}"/>'
    out += f'<rect x="340" y="790" width="920" height="30" rx="6" fill="{ink}" opacity=".55"/>'
    out += spin(800, 250, 55, 30, c)
    return out


def qukit(c):
    """Kitmon: a chain of quantum dots between two superconductors, its protected ends glowing; noise fades out."""
    ink, soft, acc = c["ink"], c["soft"], c["accent"]
    out = (f'<rect x="80" y="340" width="230" height="280" rx="30" fill="{soft}"/>'
           f'<rect x="1290" y="340" width="230" height="280" rx="30" fill="{soft}"/>'
           f'<line x1="310" y1="480" x2="1290" y2="480" stroke="{ink}" stroke-width="10" stroke-dasharray="2 26" stroke-linecap="round"/>')
    xs = [420 + i * 152 for i in range(6)]
    for i, x in enumerate(xs):
        if i in (0, len(xs) - 1):
            out += f'<circle cx="{x}" cy="480" r="120" fill="{acc}" opacity=".2"/>'
            out += spin(x, 480, 72, 0, c, arrow=False)
        else:
            out += f'<circle cx="{x}" cy="480" r="50" fill="none" stroke="{ink}" stroke-width="12"/>'
    for x0, y0, op in ((560, 170, .9), (1040, 150, .6), (800, 810, .75)):  # noise that never reaches the chain
        out += f'<g opacity="{op}">' + wave(x0 - 110, x0 + 110, y0, 22, 3, c, 10, c["muted"]) + '</g>'
    return out


def gemos(c):
    """Germanium MOSFET: gates on an oxide on germanium, a hole spin trapped just below the oxide."""
    ink, soft, acc = c["ink"], c["soft"], c["accent"]
    out = (f'<rect x="220" y="520" width="1160" height="270" rx="18" fill="{soft}"/>'
           f'<rect x="220" y="470" width="1160" height="50" rx="10" fill="{acc}" opacity=".55"/>')
    for x, w in ((330, 170), (560, 120), (740, 120), (920, 120), (1100, 170)):
        out += f'<rect x="{x}" y="330" width="{w}" height="140" rx="12" fill="{ink}"/>'
    for x in (620, 980):
        out += spin(x, 610, 60, 25 if x < 800 else -25, c)
    out += f'<path d="M620 610 Q800 700 980 610" fill="none" stroke="{c["muted"]}" stroke-width="6" stroke-dasharray="3 16" stroke-linecap="round"/>'
    return out


def humboldt(c):
    """Strong light-matter coupling: two distant spins on a chip, linked by a microwave photon in a resonator."""
    ink, soft = c["ink"], c["soft"]
    out = f'<rect x="110" y="230" width="1380" height="500" rx="40" fill="none" stroke="{soft}" stroke-width="14"/>'
    out += (f'<line x1="330" y1="430" x2="1270" y2="430" stroke="{ink}" stroke-width="12" stroke-linecap="round"/>'
            f'<line x1="330" y1="540" x2="1270" y2="540" stroke="{ink}" stroke-width="12" stroke-linecap="round"/>')
    out += wave(430, 1170, 485, 38, 2, c, 12)  # the photon between the resonator lines
    out += spin(330, 485, 100, 30, c) + spin(1270, 485, 100, -30, c)
    return out


def public_talk(c):
    """Public talk: a screen with a spin on it, the audience in front."""
    ink, soft, paper = c["ink"], c["soft"], c["paper"]
    out = (f'<rect x="440" y="70" width="720" height="440" rx="22" fill="{paper}" stroke="{ink}" stroke-width="14"/>'
           f'<line x1="800" y1="510" x2="800" y2="580" stroke="{ink}" stroke-width="12"/>')
    out += spin(800, 290, 100, 30, c)
    for i in range(7):
        x = 230 + i * 190
        out += (f'<circle cx="{x}" cy="690" r="44" fill="{soft}"/>'
                f'<path d="M{x - 78} 860 v-30 a78 78 0 0 1 156 0 v30 z" fill="{soft}"/>')
    return out


def new_website(c):
    """New website: a browser window and a phone showing the spin, the browser half light, half dark."""
    ink, soft, paper = c["ink"], c["soft"], c["paper"]
    out = (f'<clipPath id="win"><rect x="230" y="130" width="860" height="620" rx="30"/></clipPath>'
           f'<g clip-path="url(#win)"><rect x="230" y="130" width="430" height="620" fill="#ffffff"/>'
           f'<rect x="660" y="130" width="430" height="620" fill="#0f1412"/></g>'
           f'<rect x="230" y="130" width="860" height="620" rx="30" fill="none" stroke="{ink}" stroke-width="14"/>'
           f'<line x1="230" y1="220" x2="1090" y2="220" stroke="{ink}" stroke-width="12"/>')
    for i in range(3):
        out += f'<circle cx="{290 + i * 46}" cy="175" r="14" fill="{soft}"/>'
    out += spin(660, 470, 120, 30, {**c, "ink": TEAL})  # teal arrow: shows on both halves
    # the phone, overlapping the browser's lower right corner
    out += (f'<rect x="1080" y="330" width="300" height="520" rx="44" fill="{paper}" stroke="{ink}" stroke-width="14"/>'
            f'<line x1="1185" y1="380" x2="1275" y2="380" stroke="{soft}" stroke-width="12" stroke-linecap="round"/>')
    out += spin(1230, 600, 70, -30, c)
    return f'<g transform="translate(-5 0)">{out}</g>'  # browser + phone span 230..1380: centre them


def open_positions(c):
    """Open positions: a row of spins with free places, one of them waiting with a plus."""
    ink, muted, acc = c["ink"], c["muted"], c["accent"]
    out = ""
    for i, x in enumerate(range(260, 1400, 270)):
        if i in (1, 3):
            out += (f'<circle cx="{x}" cy="450" r="100" fill="none" stroke="{muted}" stroke-width="10" '
                    f'stroke-dasharray="22 18"/>'
                    f'<path d="M{x - 40} 450 h80 M{x} 410 v80" stroke="{acc}" stroke-width="16" stroke-linecap="round"/>')
        else:
            out += spin(x, 450, 100, (-25, 0, 25)[i // 2], c)
    return out


def qsit_award(c):
    """Postdoc award: a medal whose face is a spin, on two ribbons."""
    ink, soft, acc = c["ink"], c["soft"], c["accent"]
    out = (f'<polygon points="690,90 790,90 860,420 760,420" fill="{acc}" opacity=".75"/>'
           f'<polygon points="910,90 810,90 740,420 840,420" fill="{acc}"/>')
    rays = 24
    pts = []
    for k in range(2 * rays):
        r = 230 if k % 2 == 0 else 200
        a = math.pi * k / rays
        pts.append(f"{800 + r * math.sin(a):.1f},{560 - r * math.cos(a):.1f}")
    out += f'<polygon points="{" ".join(pts)}" fill="{soft}"/>'
    out += f'<circle cx="800" cy="560" r="180" fill="none" stroke="{ink}" stroke-width="12"/>'
    out += spin(800, 560, 105, 30, c)
    return out


def keynote_vek(c):
    """Keynote on simulating scalable quantum computers: a lectern next to a screen showing a grid of spins."""
    ink, soft, paper = c["ink"], c["soft"], c["paper"]
    out = f'<rect x="560" y="90" width="900" height="560" rx="24" fill="{paper}" stroke="{ink}" stroke-width="14"/>'
    for row in range(3):
        for col in range(5):
            x, y = 720 + col * 145, 210 + row * 160
            out += spin(x, y, 46, ((row * 5 + col) * 47) % 120 - 60, c)
    out += (f'<polygon points="170,520 450,520 420,820 200,820" fill="{soft}"/>'
            f'<rect x="140" y="480" width="340" height="50" rx="12" fill="{ink}"/>'
            f'<line x1="310" y1="480" x2="360" y2="400" stroke="{ink}" stroke-width="10" stroke-linecap="round"/>'
            f'<circle cx="365" cy="392" r="16" fill="{ink}"/>')
    return out


PICTURES = {
    "keynote-virtual-engine-conference-2026": keynote_vek,
    "new-website": new_website,
    "open-positions": open_positions,
    "qsit-inspire-postdoc-award": qsit_award,
    "emmy-noether-group": emmy_noether,
    "professor-in-augsburg": professor,
    "qukit-eic-pathfinder": qukit,
    "gemos-quantera-project": gemos,
    "humboldt-fellowship-beatriz-perez-gonzalez": humboldt,
    "public-talk-faszination-2026": public_talk,
}


def main(filters):
    for folder, draw in PICTURES.items():
        if filters and not any(f in folder for f in filters):
            continue
        for theme, name in (("light", "featured.png"), ("dark", "featured-dark.png")):
            svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}"><defs>{defs()}</defs>'
                   f'{draw(THEMES[theme])}</svg>')
            subprocess.run(["rsvg-convert", "-w", str(W), "-h", str(H), "-o", str(NEWS / folder / name)],
                           input=svg.encode(), check=True)
        print("drawn", folder)


if __name__ == "__main__":
    main(sys.argv[1:])
