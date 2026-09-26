## What changed and why

<!-- One or two sentences. Link an issue/ADR if there is one. -->

## Checklist

- [ ] Tests added/updated for the change (unit and/or integration)
- [ ] `mypy --strict` / `ruff check` / `ruff format --check` pass locally for every
      Python package touched (CI enforces this, but check first — see each package's README)
- [ ] Extension: `npm run typecheck && npm run lint && npm run test:extension` pass locally
- [ ] No secrets, API keys, or credentials in the diff (CI's gitleaks/push-protection will
      also catch this, but don't rely on it as the only check)
- [ ] Docs updated if this changes behavior a README/ADR documents
- [ ] If this is a significant, hard-to-reverse technical decision, an ADR is included
      (`docs/decisions/ADR-0XX-*.md`, see `docs/decisions/ADR-000-index.md`)

## PR title

Must follow [Conventional Commits](https://www.conventionalcommits.org/) —
`feat: ...`, `fix: ...`, `docs: ...`, `refactor: ...`, `test: ...`, `chore: ...`, etc.
CI checks this on every PR.
