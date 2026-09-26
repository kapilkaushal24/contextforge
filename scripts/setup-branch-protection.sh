#!/usr/bin/env bash
# Applies branch protection to `main` and `develop` matching:
#   - No direct pushes for anyone except repository admins (PR required for everyone else)
#   - PR requires >=1 approval, stale approvals dismissed on new commits, Code Owner review
#   - Every CI job below must pass before merge is allowed
#   - No force-push, no branch deletion, conversations must be resolved
#   - Repo admins can still bypass all of the above (enforce_admins=false) — this is the
#     "only an admin can force-merge" requirement; everyone else has no bypass.
#
# Cannot be run by an AI agent in a non-interactive session (GitHub's OAuth device flow
# needs a human) — run this yourself, once, after `gh auth login`. Idempotent: safe to
# re-run any time the required check list below changes (keep it in sync with
# .github/workflows/ci.yml's job `name:` fields — matrix jobs produce one check per
# matrix value).
#
# Usage:
#   gh auth login                       # one-time, interactive
#   ./scripts/setup-branch-protection.sh [owner/repo]   # defaults to the current git remote

set -euo pipefail

REPO="${1:-$(gh repo view --json nameWithOwner --jq .nameWithOwner)}"
BRANCHES=("main" "develop")

# Keep this list exactly in sync with .github/workflows/ci.yml's job `name:` fields.
REQUIRED_CHECKS='[
  {"context": "PR title (Conventional Commits)"},
  {"context": "Extension (typecheck, lint, test, build)"},
  {"context": "optimization-core (py3.12)"},
  {"context": "optimization-core (py3.14)"},
  {"context": "tokenizers"},
  {"context": "provider-adapters"},
  {"context": "optimization-service (backend)"},
  {"context": "Security scan (dependency + static analysis)"},
  {"context": "Secret scan (gitleaks)"},
  {"context": "CodeQL (python)"},
  {"context": "CodeQL (javascript-typescript)"},
  {"context": "Docker image build"}
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
echo "Verify in the GitHub UI: Settings -> Branches -> Branch protection rules."
echo "Note: required status checks only appear as selectable/enforced once each has run"
echo "at least once on this repo (push a commit or open a PR first if this is a fresh repo)."
