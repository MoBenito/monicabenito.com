"""Reads the author's list in the University of Augsburg repository (OPUS) and writes data/opus.json.

    python tools/opus.py            # refresh data/opus.json
    python tools/opus.py --list     # print every OPUS entry as JSON (used by tools/papers.py find)

The list is the "Publikationen" section of the author's page on uni-augsburg.de, which the university fills from
OPUS (the XML export of OPUS itself is closed to the public). Each entry has an OPUS id, title, DOI and, when the
library holds the full text, a link to a free PDF (usually the journal's own version, made available under the
publisher's terms, a CC licence or German secondary-publication law).

data/opus.json maps a paper's folder name to its OPUS page and PDF; the site shows a "Free PDF" link and gives
Google Scholar the PDF (citation_pdf_url). Papers are matched by DOI, or by arXiv id for preprints. Run nightly by
.github/workflows/publications.yml.
"""

import datetime
import html
import json
import re
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PAGE = "https://www.uni-augsburg.de/de/fakultaet/mntf/physik/groups/qcode/team-ag-quanteninformation-quantencomputing/monica-benito/"
UA = {"User-Agent": "monicabenito.com publication bot (https://github.com/MoBenito/monicabenito.com)"}


def text(fragment):
    return html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", fragment))).strip()


def entries():
    with urllib.request.urlopen(urllib.request.Request(PAGE, headers=UA), timeout=60) as r:
        page = r.read().decode("utf-8")
    out = []
    for block in re.findall(r'<p class="opus-document">(.*?)</p>', page, re.S):
        m = re.search(r'opus-title">\s*<a href="([^"]*docId/(\d+))"[^>]*>(.*?)</a>', block, re.S)
        if not m:
            continue
        pdf = re.search(r'href="(https://opus\.bibliothek\.uni-augsburg\.de/opus4/files/[^"]+\.pdf)"', block)
        doi = re.search(r'href="https?://(?:dx\.)?doi\.org/([^"]+)"', block)
        doi = html.unescape(doi.group(1)).strip().lower() if doi else ""
        arxiv = doi.split("arxiv.", 1)[1] if doi.startswith("10.48550/arxiv.") else ""
        year = re.search(r"\((\d{4})\)", text(re.search(r'opus-metadata">(.*?)</span>\s*<span class="opus-links', block, re.S).group(1))) \
            if 'opus-metadata"' in block else None
        out.append({"id": m.group(2), "url": m.group(1), "title": text(m.group(3)), "doi": "" if arxiv else doi,
                    "arxiv": arxiv, "pdf": pdf.group(1) if pdf else "", "year": year.group(1) if year else "",
                    "authors": text(re.search(r'opus-persons">(.*?)</span>', block, re.S).group(1)) if "opus-persons" in block else ""})
    if not out:  # page layout changed or the section is missing: better no update than an empty list
        sys.exit(f"no OPUS entries found on {PAGE}")
    return out


def site_papers():
    papers = {}
    for index in sorted((ROOT / "content" / "publications").glob("*/index.md")):
        t = index.read_text()
        one = lambda k: (m.group(1).lower() if (m := re.search(rf'^{k}: "(.*)"$', t, re.M)) else "")
        papers[index.parent.name] = {"doi": one("doi"), "arxiv": one("arxiv")}
    return papers


def main():
    found = entries()
    if "--list" in sys.argv:
        print(json.dumps(found, indent=2, ensure_ascii=False))
        return
    papers, out = site_papers(), {}
    for slug, p in papers.items():
        e = next((e for e in found if (p["doi"] and e["doi"] == p["doi"]) or (p["arxiv"] and e["arxiv"] == p["arxiv"])), None)
        if e:
            out[slug] = {"opus": e["url"], "pdf": e["pdf"]}
    data = {"source": PAGE, "updated": datetime.date.today().isoformat(), "papers": dict(sorted(out.items()))}
    path = ROOT / "data" / "opus.json"
    old = json.loads(path.read_text()) if path.exists() else {}
    if old.get("papers") != data["papers"]:  # only the date changed: leave the file alone (no daily commit)
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    print(f"{len(found)} OPUS entries, {len(out)} on the site, {sum(1 for v in out.values() if v['pdf'])} with a free PDF")


if __name__ == "__main__":
    main()
