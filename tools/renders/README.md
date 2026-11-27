# Research-area renders

Blender scenes for the pictures on the research pages. Blender 5 with Cycles (an NVIDIA GPU with OptiX makes it
fast; a full render takes a few minutes, a preview well under one). Python needs numpy and Pillow.

| Page | Scene | Extra steps |
|---|---|---|
| Topological matter | `mobius_float` | needs the blackboard texture (below) |
| Light–matter interaction | `laser_wow` | lens flare added afterwards with `flare.py` |
| Open quantum systems | `bath_wow` | none |

The spin-qubit picture was made separately and is not in this script.

## Steps

    python fetch_assets.py                     # once: CC0 HDRI and textures from Poly Haven into assets/

    # preview (960x540, few samples) or full render (1920x1080, 512 samples)
    blender -b --factory-startup --python scenes.py -- bath_wow out/bath.png preview
    blender -b --factory-startup --python scenes.py -- bath_wow out/bath.png

    # light-matter: render, then add the camera lens flare
    blender -b --factory-startup --python scenes.py -- laser_wow out/laser_raw.png
    python flare.py out/laser_raw.png out/laser.png

With the Flatpak build of Blender, run it as
`flatpak run --filesystem=$PWD --command=blender org.blender.Blender -b --factory-startup --python ...`.

Copy the result to `content/research/<area>/featured.png`. These renders are full-bleed pictures, so the pages
use `darkFigure: "original"` (no dark version).

## Blackboard texture (topological matter)

The chalkboard behind the Möbius strip is a web page: `board/make_board.py` draws the plots as hand-drawn SVG and
lets Hugo render the formulas with KaTeX; a headless Chromium takes a screenshot; `board/chalkify.py` turns it
into chalk.

    python board/make_board.py                 # writes board/site/public/
    python -m http.server 8935 --bind 127.0.0.1 -d board/site/public &    # fonts need http, not file://
    chromium --headless --hide-scrollbars --window-size=4800,2000 --virtual-time-budget=6000 \
        --screenshot=board/chalk_raw.png http://127.0.0.1:8935/
    python board/chalkify.py                   # writes board/board_tex.png, which scenes.py loads

`flare.py` takes the positions of the light sources as fractions of the image (`SOURCES`); they match the fixed
camera of `laser_wow`, so update them if the camera moves.
