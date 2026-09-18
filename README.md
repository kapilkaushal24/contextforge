# AI Token Optimizer

Chrome extension + backend service that estimates and reduces token usage in prompts sent to
AI chat tools, while preserving user intent — privacy-first, provider-agnostic, built to grow
into an enterprise product.

**Status:** Planning complete (Phases 0–2). No application code yet — see
[docs/product/development-phases.md](docs/product/development-phases.md) for what's next and
why implementation hasn't started.

## Start here

- [Product Requirements](docs/product/requirements.md)
- [System Overview & Data Flow](docs/architecture/system-overview.md)
- [Chrome Extension Architecture](docs/architecture/chrome-extension.md)
- [AI/ML Architecture & Optimization Pipeline](docs/architecture/ai-ml.md)
- [Security & Privacy](docs/security/privacy-security.md)
- [Repository Structure](docs/architecture/folder-structure.md)
- [Database ERD](docs/architecture/database-erd.md)
- [API Contracts](docs/api/contracts.md)
- [MVP Scope & Roadmap](docs/product/mvp-scope.md)
- [Development Phases](docs/product/development-phases.md)
- [Architecture Decision Records](docs/decisions/ADR-000-index.md)

## Principle

Cheapest safe transformation first: deterministic optimization before structural, structural
before semantic/LLM-assisted. Never optimize purely to minimize tokens at the cost of user
intent. Never silently modify a user's prompt without an explicit Apply.
