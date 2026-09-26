# ADR-015: CI Staged Fail-Fast, One-PR-per-Branch, Branch Lifecycle, Nightly Promotion

## Context
ADR-014 made CI a real merge gate but didn't address workflow efficiency or a few
process gaps: a broken change still burned full CI minutes across every job (nothing
stopped once one thing failed), a contributor could open multiple simultaneous PRs from
the same branch, a merged branch stayed reusable for a second PR, `main` had to be
picked manually as the PR base every time, and there was no path to keep `main` in sync
with `develop` without a human remembering to do it. This ADR covers all five.

## Decisions

**1. Fail-fast, staged pipeline.** `fail-fast: true` is now set on both matrix
strategies (`optimization-core`'s py3.12/py3.14, `codeql`'s python/javascript-typescript)
— one matrix leg failing cancels its siblings immediately, which is a real, native
GitHub Actions capability. Cross-job cancellation between *differently-named* jobs is
**not** natively supported by GitHub Actions — a job's `needs:` always waits for every
listed dependency to finish before running, so there is no built-in way to interrupt an
already-running sibling job the moment another one fails. Given that constraint, the
workflow is restaged instead: `security-scan`, `secret-scan`, and `codeql` — the three
most expensive jobs — now `needs:` all five package test/lint jobs, so they're skipped
outright (not started, not just later ignored) if any test job fails. `docker-build`
already needed `optimization-service`. Each `pytest` invocation also gained `-x`
(stop at first failing test within that job), which is the one place a genuine
mid-run "stop the rest" was achievable. A third-party action
(`styfle/cancel-workflow-action` and similar) could cancel same-stage siblings, but was
rejected: it adds an external action with `actions: write` permission for a benefit
(saving a few minutes on jobs that are already fast/parallel) that doesn't justify the
added attack surface here.

**2. Single aggregate required check (`CI Status`).** Branch protection previously had
to list all 12 individual job names, hand-kept in sync with `ci.yml` (ADR-014 flagged
this as unaddressed debt). A new `ci-status` job with `if: always()` and `needs:` on
every real job fails if any dependency failed, was cancelled, or was skipped because an
upstream job failed — `scripts/setup-branch-protection.sh` now requires only this one
check. Adding or removing a CI job no longer means updating branch protection by hand.

**3. Enterprise-CI polish**, alongside the above: `timeout-minutes` on every job (a
hung step now fails within a bounded time instead of running to the 6-hour platform
default), a top-level `permissions: contents: read` with narrow per-job overrides
(`pr-title` gets `pull-requests: write`, `one-pr-per-branch` gets `pull-requests: read`,
`codeql` keeps `security-events: write` — least privilege instead of the implicit
broad default token), `cache: pip` on every `setup-python` step (faster reruns), a
`.github/dependabot.yml` covering npm, each of the four Python packages, Docker, and
GitHub Actions itself (weekly), and CI/security status badges in `README.md`.

**4. One PR per head branch.** A new `one-pr-per-branch` job runs `gh pr list --head
<branch> --state open` on every `pull_request` event and fails if more than one is
open — a contributor with unrelated further work must branch again rather than stack a
second PR onto the same branch. Implemented as a required CI check (via `gh`, already
preinstalled on GitHub-hosted runners) rather than a repository setting, since GitHub
has no native "max concurrent open PRs per branch" option.

**5. A merged branch can't be reused.** `delete_branch_on_merge: true` is now set at
the repository level (`scripts/setup-branch-protection.sh`, `PATCH /repos/{owner}/
{repo}`) — the head branch is deleted the moment its PR merges. GitHub refuses to reopen
a PR whose head branch no longer exists, which is what actually prevents "raise another
PR from the same, already-merged branch" — there is no separate GitHub setting that
blocks PR creation from a specific branch name while leaving the branch itself in place,
so deletion is the correct lever here, not a workaround.

**6. `develop` is the default branch.** `default_branch: develop` is set the same way,
so a new PR pre-selects `develop` as its base without the author needing to change it —
matches the requested trunk being `develop`, with `main` reserved for released/promoted
code via decision 7.

**7. Nightly `develop` → `main` promotion, without bypassing review.** A new scheduled
workflow (`.github/workflows/nightly-promote.yml`, cron `30 18 * * *` = 00:00 IST) opens
or refreshes a `develop` → `main` PR and runs `gh pr merge --auto`. This only *arms*
GitHub's native auto-merge: the PR still will not merge until the required `CI Status`
check passes and the required human approval is given, exactly like any other PR against
`main`. `allow_auto_merge: true` was added as a repository setting
(`setup-branch-protection.sh`) since auto-merge is off by default. The workflow no-ops
(skips the PR entirely) when `develop` and `main` are already identical, so it doesn't
spam an empty PR every night.

## Alternatives considered
- **True bypass auto-merge for the nightly promotion** (adding the Actions bot to a
  branch-protection bypass list so it merges directly at midnight, no human approval) —
  explicitly rejected. It would mean unreviewed code reaching `main` — production —
  purely on a timer, which undoes the "only an admin can force-merge" guarantee ADR-014
  just established. Asked directly; the answer was to keep review mandatory even for
  the automated path.
- **PR-only nightly promotion with no auto-merge** — considered as the safest option,
  but rejected in favor of arming auto-merge: it achieves the same safety (still gated
  on checks + review) while actually completing the merge unattended once a human
  approves, instead of requiring someone to remember to click merge every day.
- **`styfle/cancel-workflow-action` for true cross-job cancellation** — rejected, see
  decision 1.
- **GitHub Rulesets' branch-name-pattern PR restriction, instead of
  `delete_branch_on_merge`, for "no second PR from a merged branch"** — Rulesets can
  restrict *which branches* may be PR bases/heads by pattern, but not "this specific,
  already-merged branch, and only that one" — there's no per-branch-instance rule of
  that shape in either the classic or Rulesets API. Deletion-on-merge achieves the
  actual requirement (no reopening from *that* branch) as a direct, built-in mechanic.

## Consequences
- The nightly workflow needs `allow_auto_merge: true` and a `develop` that is at least
  occasionally ahead of `main` to have anything to do; until someone runs
  `scripts/setup-branch-protection.sh` (still a manual, one-time, human step — see
  ADR-014), `gh pr merge --auto` will fail because auto-merge isn't enabled on the repo
  yet. Documented in `docs/security/branch-protection.md`.
- `security-scan`/`secret-scan`/`codeql` no longer run when a package test job fails,
  which is the intended time-saving — but it also means a security finding introduced
  alongside a failing test won't surface until the test is fixed and CI reruns. Judged
  an acceptable tradeoff: a PR with failing tests isn't mergeable regardless of what
  CodeQL would have said.
- `one-pr-per-branch` calls the GitHub API on every PR event; if GitHub's API is
  degraded this check can fail for reasons unrelated to the PR's own content, same as
  any other CI job depending on an external service.
