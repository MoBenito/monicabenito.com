"""Shared finishing grade for the paper renders: stretch the levels (1st..99.7th luminance percentile), a slight
gamma for depth, then more saturation. Gives the pale previews the bright, projector-safe look of the series.

usage: python3 grade.py in.png out.png [saturation=1.3]
"""
import sys

import numpy as np
from PIL import Image, ImageEnhance

src, dst = sys.argv[1], sys.argv[2]
sat = float(sys.argv[3]) if len(sys.argv) > 3 else 1.3
a = np.asarray(Image.open(src).convert("RGB")).astype(np.float32) / 255
lum = a.mean(2)
lo, hi = np.percentile(lum, 1), np.percentile(lum, 99.7)
b = np.clip((a - lo) / max(hi - lo, 1e-3), 0, 1) ** 1.12
out = ImageEnhance.Color(Image.fromarray((b * 255 + 0.5).astype(np.uint8))).enhance(sat)
out.save(dst)
