# ADR-014: Repository Governance — Branch Protection, PR-Only Merges, Enforced Coding Standards

## Context
Up to this point, `main` and `develop` had no protection: anyone with write access
could push directly, and CI (ADR-013) ran checks but didn't gate merges on anything —
the security-scan job was explicitly informational
(`continue-on-error: true`). The request was to close both gaps: require every change
to go through a reviewed, CI-gated PR (admins excepted, for genuine emergencies only),
and enforce "industry standard" coding conventions and production-level security
checks as real, blocking gates — not aspirational documentation.

## Decisions

**1. Ruff's lint `select` is now explicit** (`E, F, W, I, N, UP, B, C4, SIM, RUF`)
across all four Python packages, where it previously relied on ruff's version-dependent
implicit default. `N` (pep8-naming) immediately found one real violation:
`ApiException` should be `ApiError` (Python convention: exception classes end in
`Error`) — renamed throughout, including its test coverage. `UP` found six enum
classes still using the pre-3.11 `class X(str, Enum)` pattern where
`class X(StrEnum)` (Python 3.11+, and `requires-python` is already `>=3.12`) is now
idiomatic — migrated, all 213 Python tests still pass unchanged. `ruff format --check`
is now also a required step in every Python CI job, not just `ruff check` — formatting
drift is exactly as much a "coding standard" violation as a lint error, and letting it
silently accumulate defeats the point of having a formatter.

Deliberately **not** enabled: `D` (docstring rules — conflicts with this repo's
established "no comment unless the WHY is non-obvious" style, see the root coding
rules), `ANN` (redundant with `mypy --strict`, already enforced everywhere), `S`
(bandit-equivalent — real `bandit` already runs separately in CI; enabling both would
just double-report the same findings), `PL` (pylint's rule family is large and
opinionated enough to deserve its own deliberate adoption pass, not a drive-by addition
alongside everything else in this change).

**2. TypeScript gets `@typescript-eslint/naming-convention`** (camelCase
values/functions, PascalCase types/classes/components, UPPER_CASE or camelCase
constants) added to the extension's ESLint config. The existing codebase was already
fully compliant — zero violations — which is itself a useful signal that this wasn't
solving a real problem retroactively, only preventing future drift.

**3. Security scanning is now a real merge gate, not informational.**
`security-scan`'s `continue-on-error: true` (ADR-013) is removed — `pip-audit`,
`bandit`, and `npm audit --audit-level=high` all currently pass clean, so making them
blocking costs nothing today and prevents the alternative (a real finding sitting
informational, ignored, forever). Two more scanners were added, both new: **CodeQL**
(GitHub's own SAST, run for both `python` and `javascript-typescript`, integrates
natively with branch-protection required-checks and the Security tab) and
**gitleaks** (secret scanning across full git history, not just the diff — verified
locally against this exact repo's real commit history via
`docker run zricethezav/gitleaks:latest detect --source=/repo`: 10 commits scanned,
zero leaks). Gitleaks' free tier covers public repositories and individual accounts;
an organization-owned private repo would need a `GITLEAKS_LICENSE` secret — not
applicable today, documented in `docs/security/secrets-management.md` for when it is.

**4. PR title must follow Conventional Commits** (`feat:`, `fix:`, `docs:`, etc.),
enforced by `amannn/action-semantic-pull-request` as a required check — a small,
well-established, low-effort standard that also sets up clean changelog generation
later if that's ever wanted.

**5. Branch protection (classic API, not the newer Rulesets — see
`docs/security/branch-protection.md` for why) on both `main` and `develop`:** PR
required with ≥1 approval and Code Owner review, all 12 CI job names required and
`strict` (PR must be up to date with base), no force-push, no deletion, linear history,
conversation resolution required. `enforce_admins: false` is the one setting that lets
repository admins — and only admins — bypass any of this, matching "only an admin can
force-merge" exactly. **This cannot be applied by an agent in a non-interactive
session** — GitHub's branch-protection API needs an authenticated `gh` CLI or a token,
and completing `gh auth login`'s OAuth device flow needs a human. Delivered instead as
a reviewed, idempotent script (`scripts/setup-branch-protection.sh`) plus exact
documentation of what it does and how to verify it — the payload's JSON was validated
directly (extracted from the actual script file and parsed), and every required-check
name was cross-checked character-for-character against `.github/workflows/ci.yml`'s
job `name:` fields, including the two matrix jobs' auto-expanded variants.

**6. `CODEOWNERS`** (currently just the repo owner — a placeholder for team growth,
not a real change in behavior yet) and a **PR template** with a checklist, so the
human-process side of "coding standards" (did you run the checks locally, is there an
ADR for a big decision) isn't left purely to CI to catch after the fact.

## Alternatives considered
- **GitHub Rulesets instead of classic branch protection** — considered and rejected
  for now; see `docs/security/branch-protection.md`'s dedicated section. Correctness
  of a schema I could fully verify beat using the newer feature.
- **Enable `ruff`'s `S` (bandit-equivalent) rules instead of/alongside real `bandit`**
  — rejected: `bandit` is the more complete, purpose-built tool; running both would
  just duplicate findings under two different names.
- **Require 2 approvals instead of 1** — rejected as premature for a project with one
  active maintainer; `enforce_admins: false` already means the admin can merge their
  own PRs regardless, so the number mostly matters once there's more than one
  reviewer. Easy to raise later (edit the script, re-run).
- **Make CodeQL/gitleaks informational at first, promote to blocking after a trial
  period** — rejected: unlike the original informational security-scan job (which
  genuinely started with unknowns), these were verified clean against this repo's
  actual code *before* being wired in, so there was nothing to "trial."

## Consequences
- CodeQL and gitleaks-as-a-GitHub-Action have not run on a real GitHub Actions
  runner — CodeQL's SARIF upload and gitleaks' PR-comment behavior specifically depend
  on GitHub's own infrastructure and can't be replicated locally the way the other CI
  jobs were (ADR-013's "run every job's exact commands locally" approach doesn't
  extend to these two). Gitleaks was substituted with an equivalent local Docker run
  against the same source, which *does* verify the core scanning logic and confirms a
  clean result on this repo's real history — but the GitHub-integration behavior
  itself (SARIF upload, PR annotations) is unverified until the first real run.
- `scripts/setup-branch-protection.sh` requires a human to run it once — branch
  protection remains **not applied** until that happens. This ADR and
  `docs/security/branch-protection.md` describe the intended, ready-to-apply state,
  not yet the actual current state of the GitHub repository settings.
- The required-check list in the script must be kept in sync with
  `.github/workflows/ci.yml`'s job names by hand — there's no automated check that
  they match (adding one would mean the workflow can introspect and rewrite branch
  protection, a meaningfully larger and riskier addition than this repo's current
  governance maturity calls for).
