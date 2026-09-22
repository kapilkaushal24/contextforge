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
- **Phase 7** — Token estimation: `packages/tokenizers` (`OpenAITokenizer` via optional tiktoken
  with heuristic fallback, calibrated heuristics for Anthropic/Gemini/generic, `TokenizerRegistry`),
  config-driven platform→tokenizer mapping, estimated cost savings ✅
- **Phase 8** — AI optimization: structural strategy (B), LLM semantic strategy (F) behind
  `IAIProvider` (`packages/provider-adapters`: OpenAI, Anthropic), `ModelRouter` with privacy /
  mode / cost gates, deterministic safety gate on LLM output, prompt-injection trust boundary ✅
  (adapters verified against mocked transports only — not yet exercised with live API keys)
- **Phase 9** — Semantic validation: `HeuristicSemanticValidator` (deterministic, local; severity-
  weighted constraint preservation + content-word similarity + confidence capped on any hard loss),
  shared feature extractor with the LLM safety gate, `reviewReasons` exposed via the API/contracts ✅
  (heuristic and untuned — calibrate with the Phase 13 benchmark)
- **Phase 10** — Platform adapters + optimize-preview UI: `onSubmitIntercept` removed (ADR-010) in
  favor of a proactive shadow-DOM widget (`content/optimization-widget.ts`) driving a pure,
  unit-tested state machine (idle/loading/result/applied/error); Apply/Undo are the only paths
  that call `adapter.setText`; review reasons humanized for display (never raw codes) ✅
  (widget unverified against the live ChatGPT/Claude DOM — no logged-in browser session
  available in this environment; load-unpacked-and-test still needed)
- **Phase 11** — Security/privacy hardening: local PII/secrets detection
  (`optimization_core.pii`) blocks cloud LLM routing by default (ADR-011); a
  prompt-injection payload battery found and fixed two real gaps (the LLM safety gate
  and the semantic validator both let an off-topic hijacked reply through when the
  original had no hard-content markers to lose — both now check topical overlap);
  dedicated `tests/security/` suite (API-key auth, payload-limit boundaries, PII
  routing, injection battery against the live API) ✅
- **Phase 12** — Observability (ADR-012): Prometheus metrics at `GET /metrics`
  (`optimize_requests_total`, `optimize_latency_seconds`, `token_reduction_percentage`,
  `semantic_validation_failures_total`, `llm_requests_total`, `llm_latency_seconds`) —
  every one wired to a real signal, none fabricated (`cache_hit_rate` explicitly skipped,
  no cache exists yet); per-stage pipeline timing as structured, request-ID-correlated log
  lines in place of a full tracing backend; closed a real gap — added a catch-all exception
  handler so an unexpected bug returns the standard error envelope, not a leaked traceback ✅
- **Phase 13** — Testing/evaluation (unit, integration, security, eval harness) — next
- **Phase 14** — Docker/deployment (compose, CI)
- **Phase 15** — Enterprise features (orgs/teams/RBAC/policies/analytics) — post-MVP

This batch delivers Phases 0–2 plus the enterprise-readiness documents (ERD, ADRs, API
contract proposal, MVP scope) called out in the initial task. Implementation begins at Phase 3
once reviewed.
