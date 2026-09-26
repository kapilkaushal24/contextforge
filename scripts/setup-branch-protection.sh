#!/usr/bin/env bash
# Applies branch protection to `main` and `develop`, plus the repo-level settings that
# depend on it (see ADR-015), matching:
#   - No direct pushes for anyone except repository admins (PR required for everyone else)
#   - PR requires >=1 approval, stale approvals dismissed on new commits, Code Owner review
#   - The "CI Status" aggregate job (.github/workflows/ci.yml) must pass before merge —
#     it in turn requires every individual CI job, so this one check is sufficient
#   - No force-push, no branch deletion, conversations must be resolved
#   - Repo admins can still bypass all of the above (enforce_admins=false) — this is the
#     "only an admin can force-merge" requirement; everyone else has no bypass.
#   - `develop` is the repository default branch (pre-selected as a new PR's base)
#   - A branch is deleted automatically once its PR merges, so a merged branch can't be
#     reused for a second PR (GitHub blocks reopening a PR from a deleted head branch)
#   - Auto-merge is enabled repo-wide, required by the nightly develop -> main workflow
#     (.github/workflows/nightly-promote.yml), which only *arms* auto-merge — the actual
#     merge still waits on required checks + required review like any other PR
#
# Cannot be run by an AI agent in a non-interactive session (GitHub's OAuth device flow
# needs a human) — run this yourself, once, after `gh auth login`. Idempotent: safe to
# re-run any time.
#
# Usage:
#   gh auth login                       # one-time, interactive
#   ./scripts/setup-branch-protection.sh [owner/repo]   # defaults to the current git remote

set -euo pipefail

REPO="${1:-$(gh repo view --json nameWithOwner --jq .nameWithOwner)}"
BRANCHES=("main" "develop")

# Single aggregate check (see .github/workflows/ci.yml's `ci-status` job) instead of
# hand-syncing every individual job name here — closes the sync gap ADR-014 flagged.
REQUIRED_CHECKS='[
  {"context": "CI Status"}
]'

if ! command -v gh >/dev/null 2>&1; then
  echo "error: GitHub CLI ('gh') is not installed. Install it: https://cli.github.com/" >&2
  exit 1
fi

if ! gh auth status >/dev/null 2>&1; then
  echo "error: 'gh' is not authenticated. Run 'gh auth login' first (interactive)." >&2
  exit 1
fi

echo "Repository: $REPO"

echo "Setting repository defaults (default branch, delete-on-merge, auto-merge)..."
gh api \
  --method PATCH \
  -H "Accept: application/vnd.github+json" \
  "repos/${REPO}" \
  -f default_branch=develop \
  -F delete_branch_on_merge=true \
  -F allow_auto_merge=true \
  >/dev/null
echo "  done."

for branch in "${BRANCHES[@]}"; do
  echo "Applying protection to '$branch'..."
  payload=$(cat <<JSON
{
  "required_status_checks": {
    "strict": true,
    "checks": ${REQUIRED_CHECKS}
  },
  "enforce_admins": false,
  "required_pull_request_reviews": {
    "dismiss_stale_reviews": true,
    "require_code_owner_reviews": true,
    "required_approving_review_count": 1
  },
  "restrictions": null,
  "required_linear_history": true,
  "allow_force_pushes": false,
  "allow_deletions": false,
  "block_creations": false,
  "required_conversation_resolution": true,
  "lock_branch": false,
  "allow_fork_syncing": false
}
JSON
)
  echo "$payload" | gh api \
    --method PUT \
    -H "Accept: application/vnd.github+json" \
    "repos/${REPO}/branches/${branch}/protection" \
    --input - >/dev/null
  echo "  done."
done

echo
echo "Verify in the GitHub UI: Settings -> Branches -> Branch protection rules, and"
echo "Settings -> General -> Default branch / Pull Requests (auto-merge, delete head branches)."
echo "Note: required status checks only appear as selectable/enforced once each has run"
echo "at least once on this repo (push a commit or open a PR first if this is a fresh repo)."
