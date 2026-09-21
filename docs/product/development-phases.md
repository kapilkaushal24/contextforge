# Development Phases

Work proceeds incrementally; each phase produces a reviewable, testable increment. No phase
starts writing code before the prior phase's docs/interfaces are agreed.

- **Phase 0** — Product requirements ([requirements.md](./requirements.md)) ✅ this batch
- **Phase 1** — Architecture ([system-overview.md](../architecture/system-overview.md),
  ai-ml.md, chrome-extension.md, privacy-security.md) ✅ this batch
- **Phase 2** — Repository structure ([folder-structure.md](../architecture/folder-structure.md)) ✅ this batch
- **Phase 3** — Contracts/interfaces (`packages/contracts` TS types,
  `packages/optimization-core` Python domain entities + `Protocol` interfaces for
  `ITokenizer`/`IAIProvider`/`IOptimizationStrategy`/etc., [API contracts](../api/contracts.md)) ✅
- **Phase 4** — Chrome extension shell (MV3 manifest via CRXJS, background service worker,
  content script with the `IPlatformAdapter` factory wired for ChatGPT/Claude/generic, React
  popup + options pages, Tailwind, builds and lints clean) ✅
- **Phase 5** — Backend API (FastAPI skeleton: Clean Architecture layering, all `/api/v1`
  routes/DTOs from the contract doc, consistent error envelope + request-ID correlation,
  structured JSON logging, API-key auth wiring (off by default), CORS, Docker/Compose.
  Optimization logic is a documented placeholder — see
  [services/optimization-service/README.md](../../services/optimization-service/README.md)) ✅
- **Phase 6** — Deterministic optimizer (Strategy A): `DeterministicCompressionStrategy` in
  `optimization-core` (mode-tiered, code-fence-safe, idempotent, never grows text), wired into
  `/optimize` ✅
- **Phase 7** — Token estimation (`ITokenizer` implementations) — next
- **Phase 8** — AI optimization (structural + semantic compression, Model Router)
- **Phase 9** — Semantic validation
- **Phase 10** — Platform adapters (ChatGPT, Claude)
- **Phase 11** — Security/privacy hardening (PII detection, injection tests)
- **Phase 12** — Observability (structured logging, metrics, tracing)
- **Phase 13** — Testing/evaluation (unit, integration, security, eval harness)
- **Phase 14** — Docker/deployment (compose, CI)
- **Phase 15** — Enterprise features (orgs/teams/RBAC/policies/analytics) — post-MVP

This batch delivers Phases 0–2 plus the enterprise-readiness documents (ERD, ADRs, API
contract proposal, MVP scope) called out in the initial task. Implementation begins at Phase 3
once reviewed.
