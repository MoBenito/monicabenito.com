#!/usr/bin/env bash
# Writes the preview comment on a pull request: updates the existing one (found by a hidden marker) instead of
# adding a new comment on every push.
#   comment.sh <pr number> <text>
set -euo pipefail
pr="$1" body="$2
<!-- pr-preview -->"
id="$(gh api "repos/${GITHUB_REPOSITORY}/issues/${pr}/comments" --paginate \
       --jq '.[] | select(.body | contains("<!-- pr-preview -->")) | .id' | tail -n 1)"
if [ -n "$id" ]; then
  gh api -X PATCH "repos/${GITHUB_REPOSITORY}/issues/comments/${id}" -f body="$body" >/dev/null
else
  gh api -X POST "repos/${GITHUB_REPOSITORY}/issues/${pr}/comments" -f body="$body" >/dev/null
fi
