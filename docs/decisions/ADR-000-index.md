# Architecture Decision Records — Index

| ADR | Title | Status |
|---|---|---|
| [001](./ADR-001-manifest-v3.md) | Chrome Manifest V3 | Accepted |
| [002](./ADR-002-fastapi-architecture.md) | FastAPI + Clean Architecture for the backend | Accepted |
| 003 | Tokenizer abstraction (`ITokenizer` per provider) | Proposed |
| 004 | AI provider abstraction (`IAIProvider` adapter pattern) | Proposed |
| [005](./ADR-005-privacy-model.md) | Privacy model: no raw-prompt persistence by default | Accepted |
| 006 | Semantic validation gate before auto-apply | Proposed |
| 007 | Cloud vs. local inference, policy-driven via Model Router | Proposed |
| 008 | PostgreSQL for durable state + Redis for cache/rate-limit | Proposed |
| [009](./ADR-009-dynamic-platform-registry.md) | Dynamic platform registry + tab-based auto-detection (replaces the hardcoded platform enum) | Accepted |

Each ADR follows: **Context → Decision → Alternatives considered → Consequences**.
New ADRs are added as significant, hard-to-reverse technical decisions are made — not for
routine implementation choices.
