#!/usr/bin/env bash
# Puts a folder onto the gh-pages branch, or deletes one from it.
#   pages.sh put <path on gh-pages> <local folder>
#   pages.sh delete <path on gh-pages>
# Several previews can be published at the same time, so the push is retried on top of the newest gh-pages.
set -euo pipefail
action="$1" dest="$2" src="${3:-}"
work="$(mktemp -d)"
remote="https://x-access-token:${GH_TOKEN}@github.com/${GITHUB_REPOSITORY}.git"
git config --global user.name "github-actions[bot]"
git config --global user.email "41898282+github-actions[bot]@users.noreply.github.com"

for attempt in 1 2 3 4 5; do
  rm -rf "$work/site"
  if git clone --quiet --depth 1 --branch gh-pages "$remote" "$work/site" 2>/dev/null; then :; else
    # first preview ever: start an empty gh-pages branch
    git init --quiet "$work/site"; git -C "$work/site" checkout --quiet --orphan gh-pages
    git -C "$work/site" remote add origin "$remote"
    touch "$work/site/.nojekyll"
    printf '<!doctype html><meta charset="utf-8"><title>Previews</title><p>Pull request previews live in <code>pr-preview/</code>.</p>\n' > "$work/site/index.html"
  fi
  if [ "$action" = put ]; then
    rm -rf "${work:?}/site/$dest"; mkdir -p "$work/site/$dest"; cp -a "$src/." "$work/site/$dest/"
  else
    rm -rf "${work:?}/site/$dest"
  fi
  git -C "$work/site" add -A
  if git -C "$work/site" diff --cached --quiet; then echo "nothing to change"; exit 0; fi
  git -C "$work/site" commit --quiet -m "${action} ${dest}"
  if git -C "$work/site" push --quiet origin gh-pages; then echo "done: ${action} ${dest}"; exit 0; fi
  echo "gh-pages moved on, retrying ($attempt)"; sleep $((attempt * 3))
done
echo "could not update gh-pages" >&2; exit 1
