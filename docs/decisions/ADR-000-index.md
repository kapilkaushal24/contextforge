# Architecture Decision Records — Index

| ADR | Title | Status |
|---|---|---|
| [001](./ADR-001-manifest-v3.md) | Chrome Manifest V3 | Accepted |
| [002](./ADR-002-fastapi-architecture.md) | FastAPI + Clean Architecture for the backend | Accepted |
| [003](./ADR-003-tokenizer-abstraction.md) | Tokenizer abstraction (`ITokenizer` per provider) | Accepted |
| [004](./ADR-004-provider-abstraction-and-routing.md) | AI provider abstraction (`IAIProvider`) + ModelRouter (also covers 007) | Accepted |
| [005](./ADR-005-privacy-model.md) | Privacy model: no raw-prompt persistence by default | Accepted |
| [006](./ADR-006-semantic-validation.md) | Semantic validation gate before auto-apply | Accepted |
| 007 | Cloud vs. local inference, policy-driven via Model Router | Partly decided in ADR-004 (local inference still future) |
| 008 | PostgreSQL for durable state + Redis for cache/rate-limit | Proposed |
| [009](./ADR-009-dynamic-platform-registry.md) | Dynamic platform registry + tab-based auto-detection (replaces the hardcoded platform enum) | Accepted |
| [010](./ADR-010-proactive-widget-not-submit-interception.md) | Proactive optimization widget, not submit interception | Accepted |
| [011](./ADR-011-pii-detection-and-injection-hardening.md) | PII detection gate + prompt-injection hardening | Accepted |
| [012](./ADR-012-observability-scope.md) | Observability scope: Prometheus metrics + log-correlated timing, no tracing backend | Accepted |
| [013](./ADR-013-ci-docker-python314.md) | CI pipeline, Docker hardening, and the Python 3.14 / Node 24 migration | Accepted |
| [014](./ADR-014-repo-governance.md) | Repository governance: branch protection, PR-only merges, enforced coding standards | Accepted |

Each ADR follows: **Context → Decision → Alternatives considered → Consequences**.
New ADRs are added as significant, hard-to-reverse technical decisions are made — not for
routine implementation choices.
