# monicabenito.com

Personal homepage of Mónica Benito, built with [Hugo](https://gohugo.io/) and a small theme of its own (`layouts/`, `assets/css/main.css`).

## Preview

    hugo server          # http://localhost:1313/

## Content

- `content/_index.md`: home page (bio); the CV timeline comes from `data/cv.json`.
- `content/publications/<slug>/`: one folder per paper: `index.md` (title, authors, journal, DOI, arXiv, research areas, summary) and `featured.png`.
- `content/news/<slug>/`, `content/research/<slug>/`: news posts and research areas, same layout.
- Old WordPress addresses keep working through `aliases` in the front matter.

## Tools

- `python tools/darkfigs.py`: makes dark-mode versions of the figures. Each page's `darkFigure` setting chooses
  `invert` (diagrams), `cutout` (3D renders on white) or `original`. A hand-made `featured-dark.png` always wins.
- `python tools/logo.py`: regenerates the logo (`layouts/partials/logo.html`) and the favicons.
- `python tools/webfont.py`: rebuilds the self-hosted heading font (`static/fonts/outfit.woff`).

The tools need Python with fontTools, numpy and Pillow, plus `rsvg-convert` for the favicons.
