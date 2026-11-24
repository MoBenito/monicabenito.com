"""Fetches citation counts from OpenAlex and writes data/citations.json for the site.

    python tools/citations.py

Published papers are looked up by their DOI, preprints by their arXiv DOI (10.48550/arxiv.<id>). The site shows
"Cited by N" for papers with at least one citation and links it to the citing works on OpenAlex. Run it before
building (on the server: nightly, together with the build), so the numbers stay current.
"""

import datetime
import json
import re
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
UA = {"User-Agent": "monicabenito.com citation counts"}


def front(path, key):
    m = re.search(rf'^{key}: "(.*)"$', path.read_text(), re.M)
    return m.group(1) if m else ""


papers = {}
for index in sorted((ROOT / "content" / "publications").glob("*/index.md")):
    doi = front(index, "doi").lower() or (f"10.48550/arxiv.{front(index, 'arxiv')}" if front(index, "arxiv") else "")
    if doi:
        papers[doi] = index.parent.name

found = {}
dois = list(papers)
for i in range(0, len(dois), 40):
    query = urllib.parse.quote("|".join(dois[i:i + 40]), safe="|:/.")
    url = f"https://api.openalex.org/works?filter=doi:{query}&per-page=50&select=id,doi,cited_by_count"
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
        for work in json.load(r)["results"]:
            doi = work["doi"].replace("https://doi.org/", "").lower()
            found[papers[doi]] = {"count": work["cited_by_count"], "openalex": work["id"].rsplit("/", 1)[-1]}

out = {"source": "OpenAlex", "updated": datetime.date.today().isoformat(), "papers": dict(sorted(found.items()))}
(ROOT / "data" / "citations.json").write_text(json.dumps(out, indent=2) + "\n")
missing = sorted(set(papers.values()) - set(found))
print(f"{len(found)} papers, {sum(p['count'] for p in found.values())} citations" + (f"; not found: {missing}" if missing else ""))
