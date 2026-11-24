# AGENTS.md

Guidance for AI coding agents (and humans) working on this repository: the personal homepage of
Mónica Benito, a theoretical quantum physicist at the University of Augsburg. It is a Hugo site with a
small theme of its own; there is no external theme and no JavaScript build step.

## Commands

    hugo server                  # live preview at http://localhost:1313/
    hugo build --gc --minify     # must finish with no ERROR and no WARN lines
    python tools/darkfigs.py     # after adding or changing any figure
    python tools/logo.py         # only when the logo or favicon changes
    python tools/webfont.py      # only when the heading font changes

The tools need Python with fontTools, numpy and Pillow; `logo.py` also needs `rsvg-convert`.

## Layout

| Path | What it is |
|---|---|
| `hugo.toml` | Site settings, menu, contact links, author name variants to highlight |
| `content/_index.md` | Home page bio; the CV timeline comes from `data/cv.json` |
| `content/publications/<slug>/` | One folder per paper: `index.md` and `featured.png` |
| `content/news/<slug>/`, `content/research/<slug>/` | News posts and the three research areas, same pattern |
| `layouts/` | All templates. Lists use the shared card partials `pub-item.html` and `news-item.html` |
| `layouts/partials/featured.html` | Picks the light or dark figure; always use it instead of rendering `featured.*` directly |
| `assets/css/main.css` | The only stylesheet. Colours are tokens on `:root`, redefined for dark mode |
| `static/` | Favicons and the self-hosted heading font |
| `tools/` | Scripts for dark figures, logo and font |

## Adding a publication

Front matter fields (see any existing paper for an example):

```yaml
title: "…"                 # exact title; check for leftover markup from Crossref (MathML, "long-rangep-wave")
date: "YYYY-MM-DD"         # journal publication date, or the arXiv date for preprints
authors: ["…", "…"]        # full names as published
journal: "…"               # omit journal, volume, pages and doi for preprints
volume: "…"
pages: "…"
doi: "…"                   # lowercase
arxiv: "NNNN.NNNNN"        # without version suffix
research: ["spin-quantum-computing"]   # any of: spin-quantum-computing, topological-matter, open-systems-dynamics
summary: "One-sentence teaser."
darkFigure: "invert"       # written by tools/darkfigs.py; see below
aliases: ["/old-wordpress-slug/"]      # only for papers that existed on the old site
```

The body repeats the teaser as its first paragraph, then one short paragraph. Write summaries in the first
person plural, stay close to the abstract and never add claims, numbers or results the abstract does not
state. Mark them as drafts for the author to review.

Figures:
- Take the paper's Figure 1 (the first `\includegraphics` inside a figure environment) from the arXiv source.
- Render vector figures (PDF/EPS) to a PNG about 2400 px wide (`pdftoppm -scale-to-x 2400`), trim the white
  margin and add a small white border. Do not commit SVGs.
- If Figure 1 is a tall stack of panels, use only the top panel so the card stays compact.
- Check the edges for leftover frame lines or labels of the next panel.
- Save it as `featured.png`, then run `python tools/darkfigs.py`.

Every paper by the author should be on the site. ORCID has been incomplete before, so also check arXiv
(`au:Benito_M` / `au:Benito_Monica`) and Crossref. Other researchers named "M. Benito" exist; confirm before
adding anything outside quantum physics.

## Dark-mode figures

`tools/darkfigs.py` sets `darkFigure` once per page (mostly white background → `invert`, otherwise
`original`) and writes `featured-dark-auto.png`:

- `invert`: brightness flipped, colours kept, white background made transparent. For diagrams, plots and schematics.
- `cutout`: only the white background removed, colours and lighting kept. For 3D renders on white.
- `original`: no dark version. Only for photos and full-bleed renders.

A hand-made `featured-dark.png` always wins. The automatic choice is often wrong for schematics with large
coloured areas or for renders, so look at the result in dark mode and change `darkFigure` when needed.

## Conventions

- Design: Outfit for headings, menu and buttons (self-hosted, never load fonts or scripts from other
  servers), system font for body text, teal accent. Every colour comes from a token so both themes work.
- Every list item is a shared `.tile` card: the whole card is clickable via the stretched title link; extra
  links inside (Journal, arXiv) get `position: relative; z-index: 1`.
- The site must work on phones (burger menu below 640 px), in light and dark mode, with reduced motion, and
  without JavaScript.
- Links to journals and arXiv open in a new tab (`target="_blank" rel="noopener"`).
- Keep old WordPress addresses working through `aliases`.
- After editing CSS, make sure braces are balanced: a stray `}` silently drops the next rule.

## Before finishing a change

1. `hugo build --gc --minify` shows no errors or warnings.
2. Look at the changed pages at phone width (about 390 px) and desktop width, in light and dark mode.
3. Commit only when asked. Never push without the owner's explicit OK.
