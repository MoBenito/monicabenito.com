"""The description of a new-paper pull request as an editing form (used by tools/bot.py and
.github/workflows/pr-form.yml).

    python tools/prform.py apply  <description file>                 # form -> index.md; prints the page folder
    python tools/prform.py render <description file> <commit> <out>  # index.md -> form, rest of the text kept

The form lives between HTML comment markers in the description, so GitHub shows it as normal text with checkboxes:
  <!-- bot:page=<slug> -->        which page the pull request is about
  <!-- bot:figure -->...          the figure in light and dark mode (read only, refreshed from the files)
  <!-- bot:dark -->...            how dark mode shows the figure (checkboxes, one counts)
  <!-- bot:research -->...        research areas (checkboxes)
  <!-- bot:text -->...            the text on the paper page; its first paragraph is also the short summary
Ticking a box or editing the text is an edit of the description; the workflow then runs `apply`, commits, and runs
`render` to bring the description in line with the files again (so the files always win when they disagree).
"""

import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PUBS = ROOT / "content" / "publications"
REPO = os.environ.get("GITHUB_REPOSITORY", "MoBenito/monicabenito.com")
DARK = [("invert", "Automatic: brightness flipped, colours kept (diagrams on white)"),
        ("cutout", "Cut-out: only the white background removed (3D renders on white)"),
        ("original", "Original figure on a light card (photos, colour maps)")]
BLOCKS = ("figure", "dark", "research", "text")


def areas():
    out = []
    for d in sorted((ROOT / "content" / "research").iterdir()):
        if (d / "index.md").exists():
            out.append((d.name, re.search(r'^title: "(.*)"$', (d / "index.md").read_text(), re.M).group(1)))
    return out


def split(path):
    """Front matter lines and body text of an index.md."""
    t = path.read_text()
    m = re.match(r"---\n(.*?\n)---\n", t, re.S)
    return m.group(1), t[m.end():].strip()


def scalar(fm, key):
    m = re.search(rf'^{key}: "(.*)"$', fm, re.M)
    return json.loads(f'"{m.group(1)}"') if m else ""


def listed(fm, key):
    m = re.search(rf"^{key}:\n((?:  - .*\n)+)", fm, re.M)
    return [json.loads(x) for x in re.findall(r"^  - (.*)$", m.group(1), re.M)] if m else []


def set_scalar(fm, key, value):
    line = f"{key}: {json.dumps(value, ensure_ascii=False)}\n"
    fm = re.sub(rf"^{key}: .*\n", "", fm, flags=re.M)
    return fm + line if value else fm


def set_list(fm, key, values):
    fm = re.sub(rf"^{key}:\n(?:  - .*\n)+", "", fm, flags=re.M)
    return fm + f"{key}:\n" + "".join(f"  - {json.dumps(v, ensure_ascii=False)}\n" for v in values) if values else fm


def block(body, name):
    m = re.search(rf"<!-- bot:{name} -->\n?(.*?)\n?<!-- /bot:{name} -->", body, re.S)
    return m.group(1) if m else None


def ticked(text):
    return [m.group(2).strip() for m in re.finditer(r"^\s*[-*] \[([ xX])\] (.*)$", text or "", re.M) if m.group(1) != " "]


def page(body):
    m = re.search(r"<!-- bot:page=([a-z0-9-]+) -->", body)
    return m.group(1) if m and (PUBS / m.group(1) / "index.md").exists() else None


# --- form -> files ------------------------------------------------------------------------------------------------

def apply(body):
    slug = page(body)
    if not slug:
        return None
    index = PUBS / slug / "index.md"
    fm, text = split(index)
    new = block(body, "text")
    if new is not None and new.strip():
        text = new.strip().replace("\r\n", "\n")
        first = re.split(r"\n\s*\n", text, maxsplit=1)[0]
        fm = set_scalar(fm, "summary", re.sub(r"\s+", " ", first).strip())
    chosen = ticked(block(body, "research"))
    if block(body, "research") is not None:
        fm = set_list(fm, "research", [s for s, title in areas() if title in chosen])
    if block(body, "dark") is not None:
        current = scalar(fm, "darkFigure")
        modes = [mode for mode, label in DARK if label in ticked(block(body, "dark"))]
        if modes:  # if several are ticked, the one that is not the current setting is the new choice
            fm = set_scalar(fm, "darkFigure", next((m for m in modes if m != current), modes[0]))
    index.write_text(f"---\n{fm}---\n\n{text}\n")
    return slug


# --- files -> form ------------------------------------------------------------------------------------------------

def raw(sha, path):
    return f"https://raw.githubusercontent.com/{REPO}/{sha}/{path}"


def blocks(slug, sha):
    folder = PUBS / slug
    fm, text = split(folder / "index.md")
    rel = f"content/publications/{slug}"
    figure = next((p for p in sorted(folder.glob("featured.*"))), None)
    own_dark = next((p for p in sorted(folder.glob("featured-dark.*"))), None)
    dark = own_dark or (folder / "featured-dark-auto.png" if (folder / "featured-dark-auto.png").exists() else None)
    mode = scalar(fm, "darkFigure")
    if figure:
        cells = [f'<img src="{raw(sha, f"{rel}/{figure.name}")}" width="380" alt="figure">']
        if dark:
            cells.append(f'<img src="{raw(sha, f"{rel}/{dark.name}")}" width="380" alt="dark-mode figure">')
            head = "| Light mode | Dark mode" + (" (your own `featured-dark`)" if own_dark else "") + " |\n|---|---|"
        else:
            head = "| Light mode | Dark mode: the same figure on a light card |\n|---|---|"
            cells.append(f'<img src="{raw(sha, f"{rel}/{figure.name}")}" width="380" alt="figure">')
        fig = f"{head}\n| {' | '.join(cells)} |"
    else:
        fig = "⚠ No figure yet: upload a `featured.png` to the paper folder."
    dark_boxes = "\n".join(f"- [{'x' if m == mode else ' '}] {label}" for m, label in DARK)
    if own_dark:
        dark_boxes += "\n\n_Your own `featured-dark` file is used, whatever is ticked here._"
    have = set(listed(fm, "research"))
    research = "\n".join(f"- [{'x' if s in have else ' '}] {title}" for s, title in areas())
    return {"figure": fig, "dark": dark_boxes, "research": research, "text": text}


def render(body, sha):
    slug = page(body)
    if not slug:
        return body
    for name, content in blocks(slug, sha).items():
        new = f"<!-- bot:{name} -->\n{content}\n<!-- /bot:{name} -->"
        body = re.sub(rf"<!-- bot:{name} -->.*?<!-- /bot:{name} -->", lambda _: new, body, flags=re.S)
    return body


def form(slug, sha, abstract=""):
    """The form part of a new pull request's description."""
    b = blocks(slug, sha)
    folder = f"https://github.com/{REPO}/tree/{{branch}}/content/publications/{slug}"
    wrap = lambda name: f"<!-- bot:{name} -->\n{b[name]}\n<!-- /bot:{name} -->"
    abstract_part = f"\n<details><summary>arXiv abstract</summary>\n\n{abstract}\n</details>\n" if abstract else ""
    return f"""<!-- bot:page={slug} -->
### Figure
{wrap("figure")}

Another figure: upload it as `featured.png` to [the paper folder]({folder}) (Add file → Upload files, replacing the old one). Your own dark version: upload `featured-dark.png` there.

**Dark mode shows the figure as** (tick one)
{wrap("dark")}

### Research areas
{wrap("research")}

### Text on the paper page
To change it, edit this description (**···** → **Edit**) and rewrite the text between the `bot:text` markers. The first paragraph is also the short summary in the publication list.

{wrap("text")}
{abstract_part}"""


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "apply":
        print(apply(Path(sys.argv[2]).read_text()) or "")
    elif cmd == "render":
        Path(sys.argv[4]).write_text(render(Path(sys.argv[2]).read_text(), sys.argv[3]))
    else:
        sys.exit(__doc__)
