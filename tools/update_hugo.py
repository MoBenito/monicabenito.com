"""Moves the site to the newest Hugo release (run monthly by .github/workflows/update-hugo.yml).

    python tools/update_hugo.py     # prints {"from": ..., "to": ...} after updating, or nothing if up to date

Changes .hugo-version, which the workflows read (a workflow may not edit workflow files itself). Hugo renders
formulas with its built-in KaTeX, and the page styles in static/katex/ must come from the same KaTeX version, so when the new Hugo uses another KaTeX the stylesheet and
fonts are replaced too (downloaded from npm, checked against npm's checksum; woff2 fonts only).
"""

import base64
import hashlib
import io
import json
import re
import shutil
import tarfile
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VERSION_FILE = ROOT / ".hugo-version"
KATEX = ROOT / "static" / "katex"
UA = {"User-Agent": "monicabenito.com update check"}


def get(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
        return r.read()


def version(v):
    return tuple(int(x) for x in v.lstrip("v").split("."))


def update_katex(new, hugo):
    meta = json.loads(get(f"https://registry.npmjs.org/katex/{new}"))
    data = get(meta["dist"]["tarball"])
    algo, digest = meta["dist"]["integrity"].split("-", 1)
    if base64.b64encode(hashlib.new(algo, data).digest()).decode() != digest:
        raise SystemExit(f"KaTeX {new}: download does not match npm's checksum")
    with tarfile.open(fileobj=io.BytesIO(data)) as tar:
        read = lambda name: tar.extractfile(f"package/{name}").read()
        fonts = {Path(m.name).name: tar.extractfile(m).read() for m in tar.getmembers()
                 if m.isfile() and re.fullmatch(r"package/dist/fonts/[\w-]+\.woff2", m.name)}
        css = read("dist/katex.min.css").decode()
        licence = read("LICENSE")
    css = re.sub(r',url\(fonts/[^)]+\.(woff|ttf)\) format\("(woff|truetype)"\)', "", css)
    shutil.rmtree(KATEX / "fonts")
    (KATEX / "fonts").mkdir()
    for name, content in fonts.items():
        (KATEX / "fonts" / name).write_bytes(content)
    (KATEX / "katex.min.css").write_text(
        f"/* KaTeX {new} (MIT, see LICENSE), the version Hugo {hugo} renders with; woff2 fonts only */\n{css}")
    (KATEX / "LICENSE").write_bytes(licence)


def main():
    current = VERSION_FILE.read_text().strip()
    latest = json.loads(get("https://api.github.com/repos/gohugoio/hugo/releases/latest"))["tag_name"].lstrip("v")
    if version(latest) <= version(current):
        return
    VERSION_FILE.write_text(latest + "\n")
    package = json.loads(get(f"https://raw.githubusercontent.com/gohugoio/hugo/v{latest}/internal/warpc/js/package.json"))
    katex_new = package.get("dependencies", {}).get("katex") or package.get("devDependencies", {}).get("katex")
    katex_new = re.sub(r"^[\^~]", "", katex_new or "")
    katex_old = re.search(r"KaTeX ([\d.]+)", (KATEX / "katex.min.css").read_text()[:200]).group(1)
    if katex_new and katex_new != katex_old:
        update_katex(katex_new, latest)
    katex_new = katex_new or katex_old
    katex = (f"KaTeX {katex_old} → {katex_new}: the formula styles in `static/katex/` were replaced to match."
             if katex_new != katex_old else "KaTeX is unchanged.")
    body = (f"Hugo {current} → {latest} ([release notes](https://github.com/gohugoio/hugo/releases/tag/v{latest})). "
            f"{katex}\n\nIf the preview below builds and looks right (also a page with formulas, e.g. the spin-photon "
            f"paper), merge. Closing skips this version.\n\n🤖 Opened by `.github/workflows/update-hugo.yml`")
    print(json.dumps({"from": current, "to": latest, "katex_from": katex_old, "katex_to": katex_new, "body": body},
                     ensure_ascii=False))


if __name__ == "__main__":
    main()
