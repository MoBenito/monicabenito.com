"""Checks every link on the built site (run by .github/workflows/links.yml after `hugo build`).

    python tools/linkcheck.py [public] [--report report.md]

- Internal links must point to a file in the build.
- DOIs are checked at the DOI registry (doi.org/api/handles), not at the publisher: publishers often refuse
  automated visitors, which would look like broken links. arXiv ids are checked in batches through arXiv's API.
- Every other address is fetched (redirects followed). 404/410, other errors and dead hosts count as broken after a
  retry (server errors are marked as possibly temporary); answers that mean "no robots" (401, 403, 429,
  LinkedIn's 999) are listed as "could not check". OpenAlex "cited by" links are checked through its API.

Exit code 1 if anything is broken; the report (Markdown) lists each broken link with the pages that use it.
"""

import concurrent.futures
import html
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
UA = {"User-Agent": "Mozilla/5.0 (compatible; monicabenito.com link check; +https://github.com/MoBenito/monicabenito.com)"}
SITE = "https://monicabenito.com"
UNCHECKABLE = {401, 403, 429, 999}


def collect(public):
    links = defaultdict(set)  # url -> pages
    for f in public.rglob("*.html"):
        page = "/" + str(f.relative_to(public)).removesuffix("index.html")
        if page.startswith("/pr-preview/"):
            continue
        for url in re.findall(r'(?:href|src)=["\']?([^"\'\s>]+)', f.read_text(errors="replace")):
            url = html.unescape(url)
            if url.startswith(("mailto:", "tel:", "data:", "#", "javascript:")):
                continue
            if url.startswith(SITE):
                url = url[len(SITE):] or "/"
            if not url.startswith(("http://", "https://", "//")):
                url = urllib.parse.urljoin(page, url)
            links[url.split("#")[0]].add(page)
    return links


def internal_ok(public, path):
    p = public / urllib.parse.unquote(path.split("?")[0]).lstrip("/")
    return p.is_file() or (p / "index.html").is_file()


def fetch(url, method="GET"):
    req = urllib.request.Request(url, headers=UA, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, r.read(200_000)
    except urllib.error.HTTPError as e:
        return e.code, b""
    except Exception as e:  # DNS, TLS, timeout
        return None, str(e).encode()


def check_doi(doi):
    status, body = fetch("https://doi.org/api/handles/" + urllib.parse.quote(doi, safe="/"))
    if status == 200 and json.loads(body or b"{}").get("responseCode") == 1:
        return "ok", ""
    return ("broken", "DOI not registered") if status == 404 else ("retry", f"DOI registry answered {status}")


def check_arxiv(ids):
    out = {}
    for i in range(0, len(ids), 50):
        chunk = ids[i:i + 50]
        status, body = fetch("https://export.arxiv.org/api/query?max_results=100&id_list=" + ",".join(chunk))
        text = body.decode(errors="replace")
        for a in chunk:
            if status != 200:
                out[a] = ("unchecked", f"arXiv API answered {status}")
            elif re.search(rf"<id>https?://arxiv\.org/abs/{re.escape(a)}(v\d+)?</id>", text):
                out[a] = ("ok", "")
            else:
                out[a] = ("broken", "not found on arXiv")
        time.sleep(3)
    return out


def check_openalex(ids):
    """The OpenAlex web app refuses robots; one API call per 50 works tells whether they exist."""
    out = {}
    for i in range(0, len(ids), 50):
        chunk = ids[i:i + 50]
        status, body = fetch(f"https://api.openalex.org/works?per-page=50&select=id&filter=openalex:{'|'.join(chunk)}")
        got = {w["id"].rsplit("/", 1)[-1] for w in json.loads(body).get("results", [])} if status == 200 else set()
        for w in chunk:
            out[w] = ("ok", "") if w in got else ("broken", "work not found on OpenAlex") if status == 200 \
                else ("unchecked", f"OpenAlex API answered {status}")
    return out


def check_url(url):
    for attempt in range(2):
        status, body = fetch(url)
        if status and status < 400:
            return "ok", ""
        if status in UNCHECKABLE:
            return "unchecked", f"HTTP {status} (refuses automated visits)"
        if attempt == 0:
            time.sleep(5)
    if status and status >= 500:
        return "broken", f"HTTP {status} (server error, may be temporary)"
    return "broken", f"HTTP {status}" if status else body.decode(errors="replace")[:120]


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    public = Path(args[0]) if args else ROOT / "public"
    report = Path(sys.argv[sys.argv.index("--report") + 1]) if "--report" in sys.argv else None
    links = collect(public)
    results = {}
    external = [u for u in links if u.startswith(("http", "//"))]
    for u in links:
        if u not in external:
            results[u] = ("ok", "") if internal_ok(public, u) else ("broken", "no such page in the build")
    dois = {u: m.group(1) for u in external if (m := re.match(r"https?://(?:dx\.)?doi\.org/(10\..+)", u))}
    arx = {u: m.group(1) for u in external if (m := re.match(r"https?://arxiv\.org/abs/([\w./-]+?)(?:v\d+)?$", u))}
    for u, a in zip(arx, [check_arxiv(list(set(arx.values())))[a] for a in arx.values()]) if arx else []:
        results[u] = a
    oa = {u: m.group(1) for u in external if (m := re.match(r"https://openalex\.org/works\?filter=cites:(W\d+)$", u))}
    if oa:
        found = check_openalex(sorted(set(oa.values())))
        results.update({u: found[w] for u, w in oa.items()})
    rest = [u for u in external if u not in dois and u not in arx and u not in oa]
    with concurrent.futures.ThreadPoolExecutor(8) as pool:
        for u, r in zip(dois, pool.map(check_doi, dois.values())):
            results[u] = r if r[0] != "retry" else ("unchecked", r[1])
        for u, r in zip(rest, pool.map(check_url, ["https:" + u if u.startswith("//") else u for u in rest])):
            results[u] = r
    broken = sorted(u for u, (s, _) in results.items() if s == "broken")
    unchecked = sorted(u for u, (s, _) in results.items() if s == "unchecked")
    lines = [f"Checked {len(results)} links ({len(external)} external) on the built site.", ""]
    if broken:
        lines += [f"### Broken ({len(broken)})", ""]
        for u in broken:
            pages = sorted(links[u])
            lines.append(f"- `{u}`: {results[u][1]}; on {', '.join(pages[:5])}{' …' if len(pages) > 5 else ''}")
        lines.append("")
    if unchecked:
        lines += [f"<details><summary>Could not check ({len(unchecked)})</summary>", ""]
        lines += [f"- `{u}`: {results[u][1]}" for u in unchecked] + ["", "</details>"]
    text = "\n".join(lines) + "\n"
    print(text)
    if report:
        report.write_text(text)
    sys.exit(1 if broken else 0)


if __name__ == "__main__":
    main()
