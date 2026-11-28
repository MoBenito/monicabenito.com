"""Downloads the CC0 assets from Poly Haven that scenes.py uses (studio HDRI, concrete tiles) into assets/, and copies
the Nimbus Sans Bold font (from Ghostscript's fonts, package gsfonts or fonts-urw-base35) that the SymPT scene needs."""
import shutil
import urllib.request
from pathlib import Path

ASSETS = Path(__file__).parent / "assets"
FILES = {
    "studio.hdr": "https://dl.polyhaven.org/file/ph-assets/HDRIs/hdr/2k/photo_studio_01_2k.hdr",
    "tiles_diffuse.jpg": "https://dl.polyhaven.org/file/ph-assets/Textures/jpg/2k/concrete_tiles/concrete_tiles_diff_2k.jpg",
    "tiles_nor_gl.jpg": "https://dl.polyhaven.org/file/ph-assets/Textures/jpg/2k/concrete_tiles/concrete_tiles_nor_gl_2k.jpg",
    "tiles_rough.jpg": "https://dl.polyhaven.org/file/ph-assets/Textures/jpg/2k/concrete_tiles/concrete_tiles_rough_2k.jpg",
}
ASSETS.mkdir(exist_ok=True)
for name, url in FILES.items():
    dst = ASSETS / name
    if not dst.exists():
        print("downloading", name)
        req = urllib.request.Request(url, headers={"User-Agent": "research-renders"})
        dst.write_bytes(urllib.request.urlopen(req).read())

FONT = ASSETS / "sp_NimbusSans-Bold.otf"
for src in ("/usr/share/fonts/gsfonts/NimbusSans-Bold.otf", "/usr/share/fonts/opentype/urw-base35/NimbusSans-Bold.otf"):
    if not FONT.exists() and Path(src).exists():
        shutil.copy(src, FONT)
if not FONT.exists():
    print("NimbusSans-Bold.otf not found: install gsfonts (or fonts-urw-base35) for the SymPT scene")
