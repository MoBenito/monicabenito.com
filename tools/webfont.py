"""Builds the self-hosted heading font: Outfit, weights 400-600, Latin characters only, as WOFF.

    python tools/webfont.py

Writes static/fonts/outfit.woff (the font is downloaded by tools/logo.py's loader on first use).
"""

from fontTools import subset
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont

from logo import FONT_FILE, ROOT, load_font

load_font()  # makes sure the font file is there
font = instantiateVariableFont(TTFont(FONT_FILE), {"wght": (400, 600)})
options = subset.Options()
options.flavor = "woff"
options.layout_features = ["kern", "liga", "calt", "ccmp", "locl", "mark", "mkmk"]
subsetter = subset.Subsetter(options)
# Basic Latin, Latin-1 (á é í ñ ó ú ü …), Latin Extended-A, general punctuation, arrows
subsetter.populate(unicodes=[*range(0x20, 0x7F), *range(0xA0, 0x180), *range(0x2010, 0x2050), 0x2192, 0x2190])
subsetter.subset(font)
out = ROOT / "static" / "fonts" / "outfit.woff"
out.parent.mkdir(parents=True, exist_ok=True)
font.flavor = "woff"
font.save(out)
print(out, out.stat().st_size // 1024, "KB")
