"""Opens one pull request per new paper or newly published preprint (run by .github/workflows/publications.yml).

    python tools/bot.py

Needs git and the GitHub CLI (gh) with GH_TOKEN set. A change is proposed only once: if a pull request for it
exists in any state (open, merged or closed), it is skipped, so closing a pull request means "not mine / not
wanted". After opening a pull request it starts the preview workflow, because pull requests opened with the
workflow's own token do not trigger workflows by themselves.
"""

import json
import os
import re
import subprocess
import sys
from pathlib import Path

import prform  # the editable form in the pull request description

ROOT = Path(__file__).resolve().parent.parent
REPO = os.environ.get("GITHUB_REPOSITORY", "MoBenito/monicabenito.com")


def run(*cmd, capture=False):
    # Only stdout is captured; error messages go straight to the workflow log.
    r = subprocess.run(cmd, cwd=ROOT, check=True, text=True, stdout=subprocess.PIPE if capture else None)
    return r.stdout.strip() if capture else None


def proposed_branches():
    out = run("gh", "pr", "list", "--repo", REPO, "--state", "all", "--limit", "1000", "--json", "headRefName", capture=True)
    return {p["headRefName"] for p in json.loads(out)}


def branch_name(prefix, ident):
    return f"{prefix}/{re.sub(r'[^A-Za-z0-9._-]+', '-', ident).strip('-').lower()}"


def front(slug):
    t = (ROOT / "content" / "publications" / slug / "index.md").read_text()
    fm = re.match(r"---\n(.*?\n)---\n", t, re.S).group(1)
    one = lambda k: (m.group(1) if (m := re.search(rf'^{k}: "(.*)"$', fm, re.M)) else "")
    block = re.search(r"^authors:\n((?:  - .*\n)+)", fm, re.M)
    return {"title": one("title"), "journal": one("journal"), "doi": one("doi"), "arxiv": one("arxiv"),
            "authors": re.findall(r'"(.*)"', block.group(1)) if block else []}


def open_pr(branch, title, body, files):
    """body: the description, or a function of the pushed commit's hash that returns it (for links to its files)."""
    run("git", "switch", "--quiet", "-c", branch, "origin/main")
    try:
        run("git", "add", *files)
        run("git", "commit", "--quiet", "-m", title)
        run("git", "push", "--quiet", "origin", branch)
        if callable(body):
            body = body(run("git", "rev-parse", "HEAD", capture=True))
        url = run("gh", "pr", "create", "--repo", REPO, "--base", "main", "--head", branch, "--title", title, "--body", body, capture=True)
        number = url.rstrip("/").rsplit("/", 1)[-1]
        run("gh", "workflow", "run", "preview.yml", "--repo", REPO, "--ref", "main", "-f", f"pr={number}")
        print("opened", url)
    finally:
        run("git", "switch", "--quiet", "--detach", "origin/main")


def links(p):
    out = []
    if p["doi"]:
        out.append(f"[Journal](https://doi.org/{p['doi']})")
    if p["arxiv"]:
        out.append(f"[arXiv](https://arxiv.org/abs/{p['arxiv']})")
    return " · ".join(out)


def new_paper_body(found, added, branch, sha):
    p = front(added["slug"])
    who = []
    if "orcid" in found.get("identity", []) or "orcid-record" in found.get("identity", []):
        who.append("✓ listed on your ORCID record" if "orcid-record" in found["identity"] else "✓ M. Benito on this paper is linked to your ORCID iD (OpenAlex)")
    if "augsburg" in found.get("identity", []):
        who.append("✓ affiliation: University of Augsburg")
    if found.get("known_coauthors"):
        who.append("✓ known co-authors: " + ", ".join(found["known_coauthors"]))
    if not who:
        who.append("⚠ **No known co-author, no ORCID link, no Augsburg affiliation: please check this paper is yours.** "
                   "If it is not, close this pull request; it will not be proposed again.")
    figure_note = ("Figure 1 from the arXiv source (top panel only if it was a tall stack). The dark version and the "
                   "research areas are first guesses." if added.get("figure")
                   else "⚠ No figure could be taken from the arXiv source.")
    return f"""## New paper: {p['title']}

{', '.join(p['authors'])}
{p['journal'] or 'Preprint'} · {links(p)}

**Is it yours?**
{chr(10).join('- ' + w for w in who)}

**Everything below can be changed right here:** tick boxes, or edit this description to rewrite the text. The bot writes each change into the paper's page within a minute and rebuilds the preview. {figure_note} The text is a draft made from the abstract: please rewrite it.

{prform.form(added['slug'], sha, added.get('abstract', '')).replace('{branch}', branch)}
Merging publishes the paper. Closing this pull request means it will not be proposed again. A preview link follows below once it is built.

🤖 Opened by the publication bot (`.github/workflows/publications.yml`)
"""


def published_body(change, result, branch):
    p = front(change["slug"])
    return f"""## Published: {p['title']}

The preprint [arXiv:{p['arxiv']}](https://arxiv.org/abs/{p['arxiv']}) has appeared in **{result['journal']}** ([doi:{result['doi']}](https://doi.org/{result['doi']})).

This pull request only adds the journal, volume, pages, DOI and publication date{', and updates the title to the published one' if result.get('title') and result['title'] != change.get('title') else ''}. Your summary and figure stay as they are, and the arXiv link stays.

- [ ] Check the details in [`index.md`](https://github.com/{REPO}/blob/{branch}/content/publications/{change['slug']}/index.md)

Merging updates the page; closing means this update will not be proposed again.

🤖 Opened by the publication bot (`.github/workflows/publications.yml`)
"""


def main():
    changes = json.loads(run(sys.executable, "-I", "tools/papers.py", "find", capture=True))
    done = proposed_branches()
    run("git", "fetch", "--quiet", "origin", "main")
    run("git", "switch", "--quiet", "--detach", "origin/main")
    failed = []
    for found in changes["new"]:
        ident = found.get("arxiv") or found["doi"]
        branch = branch_name("paper", ident)
        if branch in done:
            continue
        try:
            run("git", "switch", "--quiet", "--detach", "origin/main")
            added = json.loads(run(sys.executable, "-I", "tools/papers.py", "add", ident, capture=True))
            run(sys.executable, "-I", "tools/darkfigs.py")
            body = lambda sha: new_paper_body(found, added, branch, sha)
            open_pr(branch, f"New paper: {added['title']}", body, [f"content/publications/{added['slug']}"])
        except Exception as err:  # e.g. arXiv not answering: leave it for the next run
            print(f"skipped {ident}: {err}", file=sys.stderr)
            failed.append(ident)
        finally:
            run("git", "reset", "--quiet", "--hard")
            run("git", "clean", "--quiet", "-fd", "content")
    for change in changes["published"]:
        branch = branch_name("published", change["slug"])
        if branch in done:
            continue
        try:
            run("git", "switch", "--quiet", "--detach", "origin/main")
            result = json.loads(run(sys.executable, "-I", "tools/papers.py", "publish", change["slug"], change["doi"], capture=True))
            open_pr(branch, f"Published: {front(change['slug'])['title']} ({result['journal']})",
                    published_body(change, result, branch), [f"content/publications/{change['slug']}/index.md"])
        except Exception as err:
            print(f"skipped {change['slug']}: {err}", file=sys.stderr)
            failed.append(change["slug"])
        finally:
            run("git", "reset", "--quiet", "--hard")
    if failed:
        sys.exit(f"not proposed this time (tried again next run): {', '.join(failed)}")


if __name__ == "__main__":
    main()
