"""Photographic lens flare as a post-process: aperture ghosts mirrored through the image centre,
a diffraction starburst from 6 aperture blades, and a faint chromatic halo ring.

usage: python3 flare.py in.png out.png [strength]
"""
import sys
import numpy as np
from PIL import Image

src, dst = sys.argv[1], sys.argv[2]
k = float(sys.argv[3]) if len(sys.argv) > 3 else 1.0
img = np.asarray(Image.open(src).convert("RGB")).astype(np.float32) / 255
lin = img ** 2.2
H, W = lin.shape[:2]
s = W / 960.0                          # sizes below are tuned at 960 px wide
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
c = np.array([W / 2, H / 2])


def box_blur(a, r):
    r = max(1, int(r))
    for ax in (0, 1):
        cs = np.cumsum(np.pad(a, [(r + 1, r) if i == ax else (0, 0) for i in range(a.ndim)], mode="edge"), axis=ax)
        n = a.shape[ax]
        a = (np.take(cs, np.arange(2 * r + 1, 2 * r + 1 + n), axis=ax) - np.take(cs, np.arange(0, n), axis=ax)) / (2 * r + 1)
    return a


# light sources: local maxima of the blurred over-bright area
lum = lin.mean(2)
hot = np.clip(lum - 0.55, 0, None)
hb = box_blur(box_blur(hot, 3 * s), 3 * s)
# the real point sources (fixed camera), as fractions of width/height, with weight
SOURCES = [(867 / 960, 256 / 540, 1.0), (622 / 960, 251 / 540, 0.8), (342 / 960, 244 / 540, 0.8), (325 / 960, 107 / 540, 0.35)]
peaks = []
for fx, fy, wt in SOURCES:
    x, y = fx * W, fy * H
    m = (xx - x) ** 2 + (yy - y) ** 2 < (6 * s) ** 2
    col = (lin[m] * hot[m][:, None]).sum(0) / (hot[m].sum() + 1e-6)
    col = col / (col.max() + 1e-6)
    peaks.append((x, y, wt, col))
wmax = max(p[2] for p in peaks)
print("sources:", [(int(x), int(y), round(w / wmax, 2)) for x, y, w, _ in peaks])

flare = np.zeros_like(lin)
rng = np.random.default_rng(7)
# ghost train: (position along source->centre->mirror, radius, opacity, coating tint)
GHOSTS = [(-0.25, 7, 0.10, (0.6, 1.0, 0.7)), (-0.55, 18, 0.045, (0.9, 0.6, 1.0)), (-0.8, 11, 0.06, (0.5, 0.9, 1.0)),
          (-1.25, 34, 0.022, (0.7, 1.0, 0.6)), (0.35, 5, 0.08, (1.0, 0.8, 0.5)), (-1.6, 55, 0.012, (0.8, 0.7, 1.0))]


def hexagon(dx, dy, r, rot=0.26):
    th = np.arctan2(dy, dx) + rot
    seg = (th % (np.pi / 3)) - np.pi / 6
    return np.hypot(dx, dy) * np.cos(seg) / (r * np.cos(np.pi / 6))   # 1 at the hexagon edge


for x, y, w, col in peaks:
    a = (w / wmax) ** 1.3
    p = np.array([x, y])
    for t, r, op, tint in GHOSTS:
        g = c + t * (p - c)
        for ch, dr in enumerate((1.03, 1.0, 0.97)):          # lateral colour: red ghost slightly larger
            d = hexagon(xx - g[0], yy - g[1], r * s * dr)
            body = np.clip((1.0 - d) / 0.12, 0, 1) * (0.55 + 0.45 * np.clip(d, 0, 1) ** 4)   # soft edge, brighter rim
            flare[..., ch] += k * a * 1.7 * op * tint[ch] * (0.5 + 0.5 * col[ch]) * body
    # starburst: thin diffraction spikes from a 6-blade aperture (12 rays), random lengths
    dx, dy = xx - x, yy - y
    r = np.hypot(dx, dy) + 1e-3
    th = np.arctan2(dy, dx)
    lens = 1 + 0.5 * rng.random(12)
    idx = (np.round((th + np.pi) / (2 * np.pi) * 12).astype(int)) % 12
    fall = 1 / (1 + (r / (6 * s)) ** 2)
    spikes = np.abs(np.cos(6 * (th - 0.26))) ** 400 * fall * np.exp(-r / (40 * s * lens[idx]))
    glow = np.exp(-r / (10 * s)) * 0.25
    for ch in range(3):
        flare[..., ch] += k * a * 0.8 * (0.35 + 0.65 * col[ch]) * (spikes + glow) * np.clip(r / (3 * s), 0, 1)
    # faint chromatic halo ring around the strongest sources only
    if a > 0.6:
        R0 = 120 * s
        for ch, off in enumerate((4, 0, -4)):
            ring = np.exp(-((r - R0 - off * s) / (5 * s)) ** 2)
            flare[..., ch] += k * a * 0.018 * ring

# slight veiling glare: very wide blur of the hot light
veil = box_blur(box_blur(lin * (lum[..., None] > 0.4), 60 * s), 60 * s)
flare += k * 0.08 * veil

out = 1 - (1 - np.clip(lin, 0, 1)) * (1 - np.clip(flare, 0, 1))     # screen blend
Image.fromarray((np.clip(out, 0, 1) ** (1 / 2.2) * 255 + 0.5).astype(np.uint8)).save(dst)
