# ADR-013: CI Pipeline, Docker Hardening, and the Python 3.14 / Node 24 Migration

## Context
Phase 14 needed three things that had never been decided or built: an actual CI
pipeline (everything up to this point had been verified by manually running
`pytest`/`mypy`/`ruff`/`npm test` by hand — real, but not enforced on every push), a
production-shaped Docker image (the existing one ran as root, no health check), and a
decision on how to handle the toolchain upgrade to Node 24 / Python 3.14 that happened
on the development machine mid-project.

## Decisions

**1. Migrate to Python 3.14 and Node 24, keep `requires-python = ">=3.12"`.**
Every `.venv` was recreated from scratch on 3.14 and every package's full test suite,
`mypy --strict`, and `ruff` were re-run — including the `tiktoken` and `pydantic-core`
Rust-extension dependencies, the two most likely to lack fresh-Python wheels. All
green, no code changes needed. The `optimization-core` CI job matrix-tests both `3.12`
and `3.14` so the declared floor is actually enforced, not just claimed. Node 24
resolved every `EBADENGINE` warning npm had been printing since Phase 4.

**2. CI is one workflow (`.github/workflows/ci.yml`) with independent jobs per
package**, mirroring how each package is developed locally (its own venv, its own
README instructions) rather than one shared environment: `extension`,
`optimization-core` (matrixed), `tokenizers`, `provider-adapters`,
`optimization-service` (with `--cov-fail-under=95`, catching a coverage regression
below Phase 13's 100%), `security-scan`, `docker-build`. Every job's exact command
sequence was verified locally against a **freshly created, isolated venv/npm install**
before being written into the workflow — not just "it worked in my long-lived dev
venv." This caught one real bug: a `working-directory: services/optimization-service`
step whose `pytest` command still used the repo-root-relative path, which would have
silently resolved to a nonexistent directory on a real runner.

**3. Security scanning (`pip-audit`, `bandit`, `npm audit`) is informational, not a merge
gate** (`continue-on-error: true` at the job level). All three ran clean against the
current codebase, but gating merges on every transitive-dependency finding without a
triage process would be brittle for a young project with four separately-versioned
Python packages. This is a deliberate, revisitable choice, not an oversight — tighten
it once there's a process for triaging findings.

**4. Docker image runs as a non-root user and declares a `HEALTHCHECK`.** The base
image moved to `python:3.14-slim`. The health check shells out to Python's own
`urllib` rather than installing `curl` (avoids an extra layer for one command) and
hits the already-unauthenticated `/healthz` route. Verified end-to-end: built the
image, ran the container, confirmed `docker inspect` reports `healthy`, confirmed
`whoami` inside the container is the unprivileged user, and confirmed
`docker compose up`/`down` builds, serves a real `/optimize` request, and tears down
cleanly.

**5. No deployment step, no registry push.** `docker-build` validates the Dockerfile
builds (with GitHub Actions cache) but never pushes anywhere — there's no registry or
deployment target configured yet, and a CI job that silently no-ops on `push` isn't
worth the false confidence of looking like it deploys something.

## Alternatives considered
- **One shared Python venv/CI job for all four packages** — rejected: masks exactly
  the kind of cross-package dependency-resolution bug (e.g. a version pin conflict)
  that separate installs catch, and doesn't match how a contributor actually works
  locally (see each package's own README).
- **Gate merges on security-scan findings immediately** — rejected for now (see
  decision 3); revisit once findings need triaging, not before.
- **Trust the workflow YAML without executing the exact commands locally** — rejected
  deliberately: "the YAML parses" is not "the commands work," and the
  `working-directory` bug above is proof that gap is real, not hypothetical.

## Consequences
- CI cannot be verified by a real GitHub Actions runner in this environment — every
  command was verified locally in an isolated, freshly created venv/npm install
  (the closest achievable proxy), but the actual workflow has not yet run on GitHub's
  infrastructure. Confirm the first real run before relying on it as a merge gate.
- The `optimization-core` matrix job roughly doubles that job's CI minutes for the
  benefit of a real floor check — worth it given it's the cheapest, dependency-free
  package to test twice.
- Deployment (pushing the built image somewhere, provisioning a target) remains
  entirely unaddressed — it's explicitly out of scope here, not silently solved.
