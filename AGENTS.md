# AGENTS.md

Guidance for AI coding agents (and humans) working on this repository: the personal homepage of
Mónica Benito, a theoretical quantum physicist at the University of Augsburg. It is a Hugo site with a
small theme of its own; there is no external theme and no JavaScript build step.

## Commands

    hugo server                  # live preview at http://localhost:1313/
    hugo build --gc --minify     # must finish with no ERROR and no WARN lines
    python tools/darkfigs.py     # after adding or changing any figure
    python tools/logo.py         # only when the logo or favicon changes
    python tools/newsart.py      # redraws the drawn news pictures (featured.png + featured-dark.png)
    python tools/webfont.py      # only when the heading font changes
    python tools/citations.py    # refreshes citation counts (data/citations.json) from OpenAlex

The tools need Python with fontTools, numpy and Pillow; `logo.py` and `newsart.py` also need `rsvg-convert`.
News posts without a photo of their own get a drawing in the logo's style: add a function to `PICTURES` in
`tools/newsart.py` (keyed by the post's folder name) and run it.

## Layout

| Path | What it is |
|---|---|
| `hugo.toml` | Site settings, menu, contact links, author name variants to highlight |
| `content/_index.md` | Home page bio; the CV timeline comes from `data/cv.json` |
| `content/publications/<slug>/` | One folder per paper: `index.md` and `featured.png` |
| `content/news/<slug>/`, `content/research/<slug>/` | News posts and the three research areas, same pattern |
| `layouts/` | All templates. Lists use the shared card partials `pub-item.html` and `news-item.html` |
| `layouts/partials/seo.html` | Share image, schema.org data (Person on the home page, ScholarlyArticle per paper) and Google Scholar `citation_*` tags; built from the front matter, nothing to fill in by hand. List pages take their meta description from `description:` |
| `layouts/partials/area-icon.html` | Small line icon per research area (paper cards, paper pages, filter, research cards); a new area needs a drawing here |
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

## Automation (GitHub Actions)

| Workflow | When | What |
|---|---|---|
| `.github/workflows/preview.yml` | every pull request | builds the site into `gh-pages` under `pr-preview/pr-<n>/`, comments the link on the PR (one comment, updated), deletes the preview when the PR is merged or closed |
| `.github/workflows/publications.yml` | nightly, or by hand | refreshes `data/citations.json` (committed to `main`), then `tools/bot.py` opens one PR per new paper (`paper/<id>`) or newly published preprint (`published/<slug>`) and starts its preview |
| `.github/workflows/deploy.yml` | push to `main`, after each Publications run, or by hand | builds with `--panicOnWarning` and uploads to the VPS over SSH (`DEPLOY_KEY` secret); see below |
| `.github/workflows/pr-form.yml` | a new-paper PR's description is edited, or files are pushed to it | keeps the description form and the page files in step (see below) |
| `.github/workflows/update-hugo.yml` | monthly, or by hand | if Hugo has a new release: PR that changes `.hugo-version` (read by all workflows) and, if its built-in KaTeX changed, replaces `static/katex/` (`tools/update_hugo.py`) |
| `.github/dependabot.yml` | monthly | one grouped PR updating the GitHub Actions the workflows use (no preview: Dependabot PRs get a read-only token) |

- New-paper PR descriptions are an editing form (`tools/prform.py`, workflow `.github/workflows/pr-form.yml`):
  figure in light and dark mode, checkboxes for the dark-mode setting and the research areas, and the page text
  between `<!-- bot:text -->` markers. Editing the description writes the change into `index.md`; pushing files
  (e.g. a new `featured.png`) makes the dark version again and refreshes the description. Files win when they
  disagree.
- `tools/papers.py find|add|publish` does the work; `tools/bot.py` only wraps it in branches and PRs. A change is
  proposed once: any PR for it, open, merged or closed, stops it from being proposed again.
- Identity checks in bot PRs: OpenAlex ORCID link, Augsburg affiliation, known co-authors. Without any of them the PR
  carries a warning; there are other researchers called M. Benito.
- Previews are built with `--environment preview` (adds `noindex`) under a subfolder, so internal links must go
  through `relURL` without a leading slash, and CSS must use relative `url(...)`.
- Repository settings: Actions > General > Workflow permissions "Read and write" plus "Allow GitHub Actions to create
  and approve pull requests"; Pages > Deploy from branch `gh-pages`. Pages needs a public repository on a free plan.

### Hosting (VPS)

- Caddy in Docker (`/opt/web/compose.yml`, `/opt/web/Caddyfile`) serves `/srv/www/current` with automatic HTTPS.
- Updates: Debian and Docker through unattended-upgrades. Container images (Caddy, later Pangolin) are to be watched
  and updated by What's Up Docker on the home server over a private WireGuard link (planned with Pangolin); until
  then update by hand: `cd /opt/web && docker compose pull && docker compose up -d`.
- The `deploy` user's key may only run `/usr/local/bin/site-receive`: it unpacks the uploaded tar into
  `/srv/www/releases/<time>`, switches the `current` link at once and keeps the last three versions. To roll back,
  point `current` at an older release.
- DNS at netcup: only `@` A/AAAA point to the VPS. The `*` wildcard and MX stay on the old netcup web hosting,
  which still runs the monicabenito.com email (`mail.monicabenito.com` resolves through the wildcard).

## Conventions

- Design: Outfit for headings, menu and buttons (self-hosted, never load fonts or scripts from other
  servers), system font for body text, teal accent. Every colour comes from a token so both themes work.
- Every list item is a shared `.tile` card: the whole card is clickable via the stretched title link; extra
  links inside (Journal, arXiv) get `position: relative; z-index: 1`.
- The site must work on phones (burger menu below 640 px), in light and dark mode, with reduced motion, and
  without JavaScript.
- Links to journals and arXiv open in a new tab (`target="_blank" rel="noopener"`).
- Every publication also gets `citation.bib` and `citation.ris` (output formats in `hugo.toml`, templates
  `layouts/publications/single.bibtex.bib` and `single.ris.ris`, key from `partials/cite-key.html`); they are
  built from the front matter, so keep authors, journal, volume, pages, DOI and arXiv correct.
- Keep old WordPress addresses working through `aliases`.
- Formulas: LaTeX in Markdown, `$...$` inline and `$$...$$` as a block. Hugo renders them with KaTeX while building
  (`layouts/_default/_markup/render-passthrough.html`); pages with formulas load `static/katex/katex.min.css`. A dollar
  sign in normal text must be escaped as `\$`.
- After editing CSS, make sure braces are balanced: a stray `}` silently drops the next rule.

## Before finishing a change

1. `hugo build --gc --minify` shows no errors or warnings.
2. Look at the changed pages at phone width (about 390 px) and desktop width, in light and dark mode.
3. Commit only when asked. Never push without the owner's explicit OK.
