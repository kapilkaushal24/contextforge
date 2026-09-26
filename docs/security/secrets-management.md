# Secrets Management

**Rule: no credential, API key, or token is ever committed to this repository — in
code, in `.env` (only `.env.example` is tracked, see `.gitignore`), in CI YAML, or in a
test fixture.** CI enforces this with `gitleaks` (scans every commit) and GitHub's own
push protection (already blocked a real push once during this project when a
deliberately-fake test fixture merely *looked* like a Slack token — see ADR-011).
Production and CI secrets live in **GitHub Actions Secrets** (or a proper secrets
manager for a real deployment target — see below), never in files.

## Local development

Every service reads configuration from environment variables via `pydantic-settings`
(`app/config/settings.py`), never hard-coded (see `services/optimization-service/
.env.example` for the full list). Copy it to `.env` (gitignored) and fill in real
values locally. `AITO_LLM_API_KEY` and any other credential-shaped setting is typed as
`pydantic.SecretStr`, which prevents it from ever appearing in a `repr()`, log line, or
exception message by accident — this is checked by a real test
(`test_api_key_is_not_exposed_in_settings_repr`, `tests/unit/test_deps.py`).

## CI (GitHub Actions Secrets)

None of the current CI jobs need a real secret — every test uses fake/mocked
providers (`FakeProvider`, `RecordingProvider`, etc.; see `docs/decisions/ADR-004`).
`GITHUB_TOKEN` (auto-provided by GitHub Actions, scoped to the current run) is the only
token any job uses today, for `gitleaks-action` and `codeql-action` to post results.

When a job *does* need a real credential (e.g. a future "verify against the live
OpenAI/Anthropic API" job — currently explicitly out of scope, see
`services/optimization-service/README.md`'s "Not yet implemented"), add it via:

**Settings → Secrets and variables → Actions → New repository secret** (or an
**Environment** secret if it should only be available to a specific deployment
environment, e.g. `production`, with optional required-reviewer approval gates on
that environment). Reference it in the workflow as `${{ secrets.NAME }}` — never
echo it, never pass it as a CLI argument (visible in process listings/logs), pass it
as an environment variable to the step that needs it instead.

```yaml
- name: Example step that needs a real key (not currently in ci.yml)
  env:
    AITO_LLM_API_KEY: ${{ secrets.AITO_LLM_API_KEY }}
  run: python -m pytest tests/live/
```

## Production deployment (when a real target exists)

No deployment target is configured yet (`docker-build` in CI only validates the image
builds — see ADR-013). When one is:

- **Prefer a managed secrets store over GitHub Secrets for the running service** —
  GitHub Secrets are for CI/build time; a deployed container should pull its runtime
  config from whatever the hosting platform's equivalent of AWS Secrets Manager / Azure
  Key Vault / GCP Secret Manager / HashiCorp Vault is, injected as environment variables
  at container start (matches the existing `pydantic-settings` pattern — no code
  change needed, just where the env vars come from).
- If deploying via a CI job that needs to authenticate to a registry or cloud provider,
  prefer short-lived OIDC federation (GitHub's `id-token: write` permission +
  the cloud provider's OIDC trust) over a long-lived static secret, where the target
  platform supports it (AWS, Azure, GCP, and most container registries do).
- Rotate anything that was ever pasted into a chat, a terminal, or a non-secrets file,
  even if it was later removed — treat it as compromised.

## If a secret ever does leak into git history

1. Rotate/revoke the credential immediately at the provider — this matters more than
   anything below, and must happen regardless of whether history is cleaned.
2. Removing it from history (`git filter-repo`, or GitHub's own secret-removal
   support) only matters for a private repo where you also want the old value
   unreadable; for a public repo assume it was already scraped the moment it was
   pushed.
