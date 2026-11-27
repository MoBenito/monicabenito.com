"""Turns the screenshot chalk_raw.png into a chalk texture: grain, uneven pressure, smudges -> board_tex.png."""
import numpy as np
from pathlib import Path
from PIL import Image, ImageFilter
HERE = Path(__file__).parent
rng = np.random.default_rng(5)
im = Image.open(HERE / "chalk_raw.png").convert("L")
W, H = im.size
m = np.asarray(im, np.float32) / 255
def blurred_noise(scale, sigma):
    n = Image.fromarray((rng.random((H // scale, W // scale)) * 255).astype(np.uint8)).resize((W, H), Image.BICUBIC)
    return np.asarray(n.filter(ImageFilter.GaussianBlur(sigma)), np.float32) / 255
grain = rng.random((H, W)).astype(np.float32)
streak = np.asarray(Image.fromarray((rng.random((H, W)) * 255).astype(np.uint8)).filter(ImageFilter.BoxBlur(2)).resize((W, H)), np.float32) / 255
pressure = 0.55 + 0.45 * blurred_noise(40, 8)
chalk = m * np.clip(0.35 + 0.9 * grain * 0.6 + 0.4 * streak, 0, 1) * pressure
chalk = np.where(grain < 0.18, chalk * 0.3, chalk)
chalk = np.asarray(Image.fromarray((np.clip(chalk, 0, 1) * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.8)), np.float32) / 255
# board: dark slate with eraser smudges and a ghost of older, wiped writing
smudge = blurred_noise(60, 30) * 0.6 + blurred_noise(12, 6) * 0.4
ghost = np.asarray(Image.fromarray((m * 255).astype(np.uint8)).transpose(Image.FLIP_LEFT_RIGHT).filter(ImageFilter.GaussianBlur(9)), np.float32) / 255
ghost2 = np.asarray(Image.fromarray((m * 255).astype(np.uint8)).transpose(Image.FLIP_TOP_BOTTOM).filter(ImageFilter.GaussianBlur(14)), np.float32) / 255
base = np.array([0.075, 0.095, 0.088])
board = base[None, None] * (0.75 + 0.5 * smudge[..., None]) + 0.10 * (ghost + ghost2)[..., None] * smudge[..., None]
board += 0.02 * (rng.random((H, W, 1)) - 0.5)
col = np.array([0.93, 0.95, 0.92])
out = board * (1 - chalk[..., None]) + col * chalk[..., None]
Image.fromarray((np.clip(out, 0, 1) ** (1 / 1.0) * 255).astype(np.uint8)).save(HERE / "board_tex.png")
Image.fromarray((np.clip(out, 0, 1) * 255).astype(np.uint8)).resize((1600, 667)).save(HERE / "board_small.png")
