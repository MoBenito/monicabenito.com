"""Finds new papers and preprint-to-journal updates, and writes page bundles for them.

    python tools/papers.py find                 # JSON: {"new": [...], "published": [...]}
    python tools/papers.py add <arxiv id>       # create content/publications/<slug>/ (details, figure, draft summary)
    python tools/papers.py publish <slug> <doi> # add journal details to an existing preprint page

Used by .github/workflows/publications.yml, which opens one pull request per change. Sources:
- arXiv (author "M. Benito" / "Mónica Benito" in quant-ph, cond-mat and physics): catches preprints, including ones
  missing from ORCID;
- ORCID works and OpenAlex (by ORCID iD): catch journal papers;
- Crossref: journal details by DOI, and the journal version of a preprint by title.
Figures: Figure 1 from the arXiv source (first \\includegraphics in a figure), rendered about 2400 px wide; if
it is a tall stack of panels, only the top panel. Summaries are drafts made from the abstract and must be
reviewed in the pull request.
"""

import difflib
import html
import json
import re
import subprocess
import sys
import tarfile
import gzip
import tempfile
import time
import urllib.parse
import urllib.request
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
PUBS = ROOT / "content" / "publications"
ORCID = "0000-0001-6365-9505"
ME = {"M. Benito", "Mónica Benito", "Monica Benito"}
UA = {"User-Agent": "monicabenito.com publication bot (https://github.com/MoBenito/monicabenito.com)"}
AREAS = {  # keywords for suggesting a research area; the pull request asks to confirm
    "spin-quantum-computing": ["spin qubit", "quantum dot", "spin-photon", "electron spin", "hole spin", "edsr",
                               "flopping", "readout", "resonator", "solid neon", "helium", "two-qubit", "qubit"],
    "topological-matter": ["topolog", "majorana", "kitaev", "edge state", "quantum geometr", "flat band", "caging"],
    "open-systems-dynamics": ["floquet", "dissipat", "open quantum", "lindblad", "decoherence", "driven",
                              "transport", "counting statistics", "master equation", "perturbative"],
}


def get(url, as_json=False, tries=5):
    for i in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
                data = r.read()
            return json.loads(data) if as_json else data
        except Exception as err:
            print(f"{url}: {err}", file=sys.stderr)
            if i == tries - 1:
                raise
            # arXiv often answers GitHub's servers with 429 (too many requests): wait longer then
            throttled = getattr(err, "code", None) in (429, 503)
            wait = 30 * 2 ** i if throttled else 3 * (i + 1)
            try:
                wait = max(wait, int(err.headers.get("Retry-After", 0)))
            except (AttributeError, TypeError, ValueError):
                pass
            time.sleep(min(wait, 300))


def norm_title(t):
    return re.sub(r"[^a-z0-9]", "", t.lower())


def front(path):
    t = path.read_text()
    m = re.match(r"---\n(.*?\n)---\n", t, re.S)
    fm = m.group(1)
    one = lambda k: (x.group(1) if (x := re.search(rf'^{k}: "(.*)"$', fm, re.M)) else "")
    return {"slug": path.parent.name, "title": one("title"), "doi": one("doi").lower(), "arxiv": one("arxiv"),
            "journal": one("journal")}


def existing():
    return [front(p) for p in sorted(PUBS.glob("*/index.md"))]


def surname(name):
    return re.sub(r"[^a-z]", "", name.split()[-1].lower()) if name.strip() else ""


def known_coauthors():
    """Surnames of everyone on the site's papers, to tell this M. Benito apart from others with that name."""
    names = set()
    for p in PUBS.glob("*/index.md"):
        a = re.search(r"authors:\n((?:  - .*\n)+)", p.read_text())
        names |= {surname(x) for x in re.findall(r'"(.*)"', a.group(1))} if a else set()
    return names - {"benito"}


# --- sources -------------------------------------------------------------------------------------------

def arxiv_entries(query="", ids=()):
    url = ("https://export.arxiv.org/api/query?" +
           (f"id_list={','.join(ids)}&max_results=100" if ids else f"search_query={query}&max_results=200"))
    feed = get(url).decode()
    out = []
    for e in re.findall(r"<entry>(.*?)</entry>", feed, re.S):
        f = lambda tag: (m.group(1).strip() if (m := re.search(rf"<{tag}[^>]*>(.*?)</{tag}>", e, re.S)) else "")
        authors = [html.unescape(a) for a in re.findall(r"<name>(.*?)</name>", e)]
        out.append({"arxiv": re.search(r"arxiv.org/abs/([^<v]+)", e).group(1),
                    "title": re.sub(r"\s+", " ", html.unescape(f("title"))), "authors": authors,
                    "date": f("published")[:10], "abstract": re.sub(r"\s+", " ", html.unescape(f("summary"))),
                    "doi": f("arxiv:doi").lower(), "journal_ref": f("arxiv:journal_ref")})
    return out


def my_arxiv_papers():
    # arXiv's author search does not match "Mónica" under "M", so ask for each spelling and merge
    found = {}
    for author in ("Benito_M", "Benito_Monica", "Benito_M%C3%B3nica"):
        for e in arxiv_entries(query=f"au:{author}+AND+(cat:quant-ph+OR+cat:cond-mat*+OR+cat:physics*)"):
            if ME & set(e["authors"]):
                found[e["arxiv"]] = e
        time.sleep(3)  # arXiv asks for a pause between requests
    return list(found.values())


def crossref(doi):
    m = get(f"https://api.crossref.org/works/{urllib.parse.quote(doi)}", as_json=True)["message"]
    parts = (m.get("published-print") or m.get("published-online") or m.get("issued"))["date-parts"][0]
    title = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", (m.get("title") or [""])[0]))).strip()
    return {"title": title, "journal": (m.get("container-title") or [""])[0], "volume": m.get("volume") or "",
            "pages": m.get("page") or m.get("article-number") or "", "doi": doi.lower(),
            "date": "-".join(f"{x:02d}" for x in (parts + [1, 1])[:3]),
            "authors": [f"{a.get('given', '')} {a.get('family', '')}".strip() for a in m.get("author", [])]}


def journal_version(entry):
    """DOI of the journal version of an arXiv preprint, from arXiv itself or a Crossref title search."""
    if entry.get("doi"):
        return entry["doi"]
    r = get("https://api.crossref.org/works?rows=5&filter=type:journal-article&query.title=" +
            urllib.parse.quote(entry["title"]), as_json=True)
    for it in r["message"]["items"]:
        t = html.unescape(re.sub(r"<[^>]+>", "", (it.get("title") or [""])[0]))
        if (difflib.SequenceMatcher(None, norm_title(t), norm_title(entry["title"])).ratio() > 0.9
                and any("Benito" in a.get("family", "") for a in it.get("author", []))):
            return it["DOI"].lower()
    return ""


def orcid_dois():
    req = urllib.request.Request(f"https://pub.orcid.org/v3.0/{ORCID}/works", headers={**UA, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        groups = json.load(resp)["group"]
    out = []
    for g in groups:
        s = g["work-summary"][0]
        ids = {i["external-id-type"]: i["external-id-value"] for i in s["external-ids"]["external-id"]}
        if ids.get("doi"):
            out.append({"doi": ids["doi"].lower(), "title": s["title"]["title"]["value"]})
    return out


def identity_check(arxiv_id="", doi=""):
    """How OpenAlex lists our M. Benito on a paper: linked to the ORCID iD, and/or at the University of Augsburg.
    Returns a list of short findings (empty when OpenAlex does not know the paper yet)."""
    found = []
    for d in [x for x in (doi, f"10.48550/arxiv.{arxiv_id}" if arxiv_id else "") if x]:
        try:
            w = get(f"https://api.openalex.org/works/doi:{urllib.parse.quote(d, safe='/:.')}", as_json=True)
        except Exception:
            continue
        for a in w.get("authorships", []):
            if "benito" not in (a.get("author", {}).get("display_name") or "").lower():
                continue
            if (a["author"].get("orcid") or "").endswith(ORCID):
                found.append("orcid")
            if any("augsburg" in (i.get("display_name") or "").lower() for i in a.get("institutions", [])):
                found.append("augsburg")
        if found:
            break
    return sorted(set(found))

# --- finding changes ---------------------------------------------------------------------------------------

def find():
    have = existing()
    known_arxiv = {p["arxiv"] for p in have if p["arxiv"]}
    known_doi = {p["doi"] for p in have if p["doi"]}
    known_title = {norm_title(p["title"]) for p in have}
    coauthors = known_coauthors()
    new, published = [], []
    try:
        mine = my_arxiv_papers()
    except Exception as err:
        # Without the arXiv list an ORCID entry could be proposed a second time under its DOI, so skip it all.
        print(f"arXiv did not answer ({err}); no search this time, the next run tries again", file=sys.stderr)
        return {"new": [], "published": []}
    for e in mine:
        if e["arxiv"] in known_arxiv or norm_title(e["title"]) in known_title:
            continue
        shared = sorted({surname(a) for a in e["authors"]} & coauthors)
        new.append({"arxiv": e["arxiv"], "title": e["title"], "date": e["date"], "known_coauthors": shared,
                    "identity": identity_check(arxiv_id=e["arxiv"], doi=e["doi"])})
    for w in orcid_dois():  # journal papers on ORCID without an arXiv version we already matched
        if w["doi"] in known_doi or norm_title(w["title"]) in known_title:
            continue
        if any(difflib.SequenceMatcher(None, norm_title(w["title"]), norm_title(n["title"])).ratio() > 0.9 for n in new):
            continue
        new.append({"doi": w["doi"], "title": w["title"], "known_coauthors": [], "identity": ["orcid-record"]})
    preprints = [p for p in have if p["arxiv"] and not p["journal"]]
    try:
        entries = arxiv_entries(ids=[p["arxiv"] for p in preprints]) if preprints else []
    except Exception as err:
        print(f"arXiv did not answer ({err}); preprints are checked again next run", file=sys.stderr)
        entries = []
    if entries:
        for e in entries:
            doi = journal_version(e)
            if doi:
                slug = next(p["slug"] for p in preprints if p["arxiv"] == e["arxiv"])
                published.append({"slug": slug, "doi": doi, "title": e["title"]})
            time.sleep(1)
    return {"new": new, "published": published}


# --- writing bundles -----------------------------------------------------------------------------------------

def slugify(title):
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", title.lower())).strip("-")[:80].rstrip("-")


def suggest_areas(title, abstract):
    text = f"{title} {abstract}".lower()
    scores = {a: sum(text.count(k) for k in kws) for a, kws in AREAS.items()}
    best = sorted((s, a) for a, s in scores.items() if s > 0)[::-1]
    return [a for s, a in best[:2] if s >= max(2, best[0][0] // 2)] if best else []


def draft_summary(abstract):
    sentences = re.split(r"(?<=[.!?])\s+(?=[A-Z])", abstract.strip())
    teaser = sentences[0]
    body = " ".join(sentences[1:]) or abstract
    return teaser, body


def figure_from_arxiv(arxiv_id, out_png):
    """Figure 1 of the arXiv source as a PNG ~2400 px wide; top panel only for tall figure stacks."""
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        src = tmp / "src"
        src.write_bytes(get(f"https://arxiv.org/e-print/{arxiv_id}"))
        root = tmp / "x"
        root.mkdir()
        try:
            with tarfile.open(src) as t:
                t.extractall(root, filter="data")
        except tarfile.ReadError:
            try:
                (root / "main.tex").write_bytes(gzip.open(src).read())
            except OSError:
                return False
        texs = list(root.rglob("*.tex"))
        if not texs:
            return False
        main = max(texs, key=lambda p: ("\\begin{document}" in p.read_text(errors="ignore"), p.stat().st_size))
        tex = re.sub(r"(?<!\\)%.*", "", main.read_text(errors="ignore"))
        tex = re.sub(r"\\(?:input|include)\{([^}]+)\}", lambda m: (main.parent / (m.group(1) if m.group(1).endswith(".tex") else m.group(1) + ".tex")).read_text(errors="ignore") if (main.parent / (m.group(1) if m.group(1).endswith(".tex") else m.group(1) + ".tex")).exists() else "", tex)
        gp = re.findall(r"\\graphicspath\{\s*((?:\{[^}]*\}\s*)+)\}", tex)
        dirs = [""] + (re.findall(r"\{([^}]*)\}", gp[0]) if gp else [])
        inc = None
        for fig in re.findall(r"\\begin\{figure\*?\}(.*?)\\end\{figure\*?\}", tex, re.S):
            m = re.findall(r"\\includegraphics\*?(?:\[[^\]]*\])?\{([^}]*)\}", fig)
            if m:
                inc = m[0].strip()
                break
        if not inc:
            return False
        cands = [main.parent / d / (inc + ext) for d in dirs for ext in ("", ".pdf", ".png", ".jpg", ".jpeg", ".PNG", ".JPG", ".eps")]
        path = next((c for c in cands if c.is_file()), None)
        if not path:
            return False
        raw = tmp / "fig.png"
        ext = path.suffix.lower()
        if ext == ".pdf":
            subprocess.run(["pdftoppm", "-png", "-singlefile", "-scale-to-x", "2400", "-scale-to-y", "-1", str(path), str(raw.with_suffix(""))], check=True)
        elif ext == ".eps":
            subprocess.run(["gs", "-q", "-dSAFER", "-dBATCH", "-dNOPAUSE", "-dEPSCrop", "-sDEVICE=png16m", "-r600", f"-sOutputFile={raw}", str(path)], check=True)
        else:
            Image.open(path).save(raw)
        im = Image.open(raw).convert("RGBA")
        bg = Image.new("RGBA", im.size, "white")
        bg.alpha_composite(im)
        a = np.asarray(bg.convert("RGB"))
        white = (a.min(-1) > 245).mean(1) > 0.995
        if a.shape[0] > a.shape[1] * 1.1:  # tall stack of panels: cut at the first blank gap below 15 %
            run, h = 0, a.shape[0]
            start = int(np.argmax(~white))
            for y in range(start + int(0.15 * h), h):
                run = run + 1 if white[y] else 0
                if run >= 12:
                    a = a[:y - run + 1]
                    break
        mask = a.min(-1) < 245
        ys, xs = np.where(mask)
        if len(ys):
            a = a[max(0, ys.min() - 24):ys.max() + 25, max(0, xs.min() - 24):xs.max() + 25]
        Image.fromarray(a).save(out_png, optimize=True)
        return True


def write_bundle(slug, fm, body):
    lines = ["---"]
    for k, v in fm.items():
        if v in (None, "", []):
            continue
        if isinstance(v, list):
            lines.append(f"{k}:")
            lines += [f"  - {json.dumps(x, ensure_ascii=False)}" for x in v]
        else:
            lines.append(f"{k}: {json.dumps(str(v), ensure_ascii=False)}")
    lines += ["---", "", body.strip(), ""]
    (PUBS / slug).mkdir(parents=True, exist_ok=True)
    (PUBS / slug / "index.md").write_text("\n".join(lines))


def add(ident):
    if re.match(r"^\d{4}\.\d{4,5}$", ident):
        e = arxiv_entries(ids=[ident])[0]
        doi = journal_version(e)
        meta = crossref(doi) if doi else {}
    else:
        meta = crossref(ident)
        hits = arxiv_entries(query="ti:%22" + urllib.parse.quote(re.sub(r"[^A-Za-z0-9 ]", " ", meta["title"])) + "%22")
        e = next((h for h in hits if difflib.SequenceMatcher(None, norm_title(h["title"]), norm_title(meta["title"])).ratio() > 0.9), None)
        e = e or {"arxiv": "", "title": meta["title"], "authors": meta["authors"], "date": meta["date"], "abstract": ""}
    title = meta.get("title") or e["title"]
    slug = slugify(title)
    teaser, body = draft_summary(e["abstract"]) if e["abstract"] else ("", "")
    fm = {"title": title, "date": meta.get("date") or e["date"], "authors": meta.get("authors") or e["authors"],
          "journal": meta.get("journal"), "volume": meta.get("volume"), "pages": meta.get("pages"),
          "doi": meta.get("doi"), "arxiv": e["arxiv"], "research": suggest_areas(title, e["abstract"]),
          "summary": teaser}
    write_bundle(slug, fm, f"{teaser}\n\n{body}" if teaser else "")
    fig = e["arxiv"] and figure_from_arxiv(e["arxiv"], PUBS / slug / "featured.png")
    print(json.dumps({"slug": slug, "title": title, "figure": bool(fig), "research": fm["research"],
                      "journal": fm["journal"] or "preprint", "arxiv": e["arxiv"], "doi": fm["doi"]}))


def publish(slug, doi):
    path = PUBS / slug / "index.md"
    meta = crossref(doi)
    t = path.read_text()
    m = re.match(r"---\n(.*?\n)---\n", t, re.S)
    fm = m.group(1)
    fm = re.sub(r'^date: ".*"$', f'date: "{meta["date"]}"', fm, flags=re.M)
    extra = "".join(f'{k}: {json.dumps(meta[k], ensure_ascii=False)}\n' for k in ("journal", "volume", "pages", "doi") if meta[k])
    fm = re.sub(r'^(arxiv: ".*"\n)', extra + r"\1", fm, flags=re.M)
    old_title = re.search(r'^title: "(.*)"$', fm, re.M).group(1)
    if meta["title"] and norm_title(meta["title"]) != norm_title(old_title):
        fm = re.sub(r'^title: ".*"$', f'title: {json.dumps(meta["title"], ensure_ascii=False)}', fm, flags=re.M)
    path.write_text(t[:m.start(1)] + fm + t[m.end(1):])
    print(json.dumps({"slug": slug, "journal": meta["journal"], "doi": doi, "title": meta["title"] or old_title}))


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "find"
    if cmd == "find":
        print(json.dumps(find(), indent=2, ensure_ascii=False))
    elif cmd == "add":
        add(sys.argv[2])
    elif cmd == "publish":
        publish(sys.argv[2], sys.argv[3])
    else:
        sys.exit(__doc__)
