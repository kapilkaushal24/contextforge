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

Each ADR follows: **Context → Decision → Alternatives considered → Consequences**.
New ADRs are added as significant, hard-to-reverse technical decisions are made — not for
routine implementation choices.
