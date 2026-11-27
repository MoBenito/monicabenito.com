"""Downloads the CC0 assets from Poly Haven that scenes.py uses (studio HDRI, concrete tiles) into assets/."""
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
