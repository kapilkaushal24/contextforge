# Branch Protection & Repository Rules

Enforces: nobody pushes directly to `main` or `develop` — every change goes through a
PR — and a PR cannot merge unless every CI check below passes. Only repository admins
can bypass this (to force-merge in a genuine emergency); no one else has a bypass path.

## Why this isn't already applied

Branch protection is a GitHub repository *setting*, not something in this codebase's
files — it lives on GitHub's servers and can only be changed by someone authenticated
to the GitHub API (via `gh auth login`, a personal access token, or the web UI). An AI
agent in a non-interactive session cannot complete GitHub's OAuth device flow, and
should not be handed a token to do this on your behalf — so this is a one-time step
you run yourself.

## Apply it (one-time, ~30 seconds)

```bash
# Install the GitHub CLI if you don't have it: https://cli.github.com/
gh auth login              # interactive — opens a browser
./scripts/setup-branch-protection.sh
```

This calls the classic Branch Protection REST API (`PUT /repos/{owner}/{repo}/branches/
{branch}/protection`) for both `main` and `develop` with:

| Setting | Value | Effect |
|---|---|---|
| `required_pull_request_reviews` | ≥1 approval, stale reviews dismissed on new commits, Code Owner review required | No direct commits merge in — every change is reviewed |
| `required_status_checks` | all 12 CI job names below, `strict: true` | PR must be up to date with the base branch AND every job green |
| `enforce_admins` | `false` | **Repo admins can bypass all of the above** (the "only admin can force-merge" requirement) — everyone else cannot |
| `restrictions` | `null` | No separate push-allowlist beyond what PR-required already enforces |
| `allow_force_pushes` | `false` | No rewriting protected-branch history |
| `allow_deletions` | `false` | `main`/`develop` cannot be deleted |
| `required_linear_history` | `true` | No merge commits with multiple parents polluting history |
| `required_conversation_resolution` | `true` | Every PR review comment thread must be resolved before merge |

### Required status checks (must match `.github/workflows/ci.yml` job names exactly)

1. `PR title (Conventional Commits)`
2. `Extension (typecheck, lint, test, build)`
3. `optimization-core (py3.12)`
4. `optimization-core (py3.14)`
5. `tokenizers`
6. `provider-adapters`
7. `optimization-service (backend)`
8. `Security scan (dependency + static analysis)`
9. `Secret scan (gitleaks)`
10. `CodeQL (python)`
11. `CodeQL (javascript-typescript)`
12. `Docker image build`

GitHub only lets you require a check that has run at least once — if this is a brand
new repo, push once or open one PR first so the workflow runs, *then* apply the script
(it's idempotent; re-run any time).

## Verify

GitHub Settings → **Branches** → the rule for `main` and for `develop`. Confirm "Require
a pull request before merging", the review count, the full status-check list, and that
"Do not allow bypassing the above settings" is **unchecked** (that's what lets admins,
and only admins, bypass — checking it would block even admins, which isn't what was
asked for here).

## Classic protection vs. Rulesets

GitHub's newer "Rulesets" feature can express the same policy and adds a few extras
(e.g. richer bypass-actor targeting by team, not just "admin"). This repo uses the
classic branch-protection API because its JSON schema is simpler, stable, and has been
documented unchanged for years — correctness was prioritized over using the newest
feature. If the team grows past "one admin, everyone else a contributor," revisit
Rulesets for more granular bypass rules (e.g. "release manager" team, not just Admin).

## What CI actually checks (and where the source of truth is)

See `.github/workflows/ci.yml` directly, and `docs/decisions/ADR-013-ci-docker-
python314.md` / `docs/decisions/ADR-014-repo-governance.md` for why each check exists.
Summary: type checks (`mypy --strict`), lint + formatting + naming convention (`ruff
check` / `ruff format --check` with pep8-naming enabled, ESLint with
`@typescript-eslint/naming-convention`), full test suites with a coverage floor,
dependency vulnerability scanning (`pip-audit`, `npm audit`), static security analysis
(`bandit`, CodeQL for both Python and JS/TS), secret scanning (`gitleaks`, plus
GitHub's native push protection which already blocked a real push once during this
project — see ADR-011), a Docker image build, and PR title format (Conventional
Commits).
