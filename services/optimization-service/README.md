# optimization-service

FastAPI backend implementing the `/api/v1/*` surface described in
[docs/api/contracts.md](../../docs/api/contracts.md). This is the **Phase 5 skeleton**: routing,
DTOs, error handling, request correlation, and Clean Architecture layering are real and tested;
`/optimize` now runs the **deterministic strategy** (Phase 6: whitespace cleanup, exact duplicate
line/sentence removal, aggressive-mode pleasantry removal; fenced code never touched; no LLM).
Token counts come from per-provider tokenizers (Phase 7, `packages/tokenizers`; always labeled
`estimated`), and `estimatedCostSaved` uses the configurable `AITO_INPUT_PRICE_PER_1K_USD`.
**LLM optimization (Phase 8)** is off by default. Set `AITO_ENABLE_LLM_OPTIMIZATION=true`,
`AITO_LLM_PROVIDER` (`openai`|`anthropic`), `AITO_LLM_MODEL` and `AITO_LLM_API_KEY`. The
`ModelRouter` then calls it only for non-code prompts in balanced/aggressive/context mode, never
under `local_only` privacy, and only when its estimated cost is below the estimated savings.
Any LLM failure or unsafe rewrite falls back to the deterministic result.
**Validation (Phase 9):** every result is scored by a deterministic `HeuristicSemanticValidator`
(ADR-006). `/optimize` returns `confidence`, `semanticSimilarity`, `constraintPreservation`,
`requiresReview` and `reviewReasons`; `/validate` scores any original/optimized pair. A dropped
negation, number, identifier, quote or code block caps confidence at 0.5, forcing review.
`/analyze` does rule-based code-vs-general detection; its redundancy signal is still a placeholder.
**Security hardening (Phase 11, ADR-011):** `optimization_core.pii.detect_pii` (local,
deterministic — email/phone/SSN/credit-card/API-key) blocks cloud LLM routing by default
regardless of `privacyPolicy` (`AITO_BLOCK_PII_FROM_CLOUD`); detected categories are reported in
`sensitiveContentCategories`, never the matched text. A prompt-injection payload battery
(`tests/security/`) found and fixed two real defects: the LLM safety gate and the semantic
validator both let an unrelated hijacked reply through when the original prompt had no
numbers/identifiers/quotes/negations to lose — both now also check topical overlap
(`topic_drift`).

## Layering

`api/` (routes + Pydantic DTOs) → `application/` (use cases, e.g. `optimize_use_case.py`) →
`optimization_core` (the shared domain package: entities + `Protocol` interfaces, from
`packages/optimization-core`). Routes never contain business logic; they map DTOs to/from domain
objects and call a use case.

## Develop

```bash
python -m venv .venv
./.venv/Scripts/python.exe -m pip install -e "../../packages/optimization-core"   # domain package
./.venv/Scripts/python.exe -m pip install -e "../../packages/tokenizers[openai]"    # tokenizers (tiktoken optional)
./.venv/Scripts/python.exe -m pip install -e "../../packages/provider-adapters"      # OpenAI/Anthropic adapters
./.venv/Scripts/python.exe -m pip install -e ".[dev]"                              # this service
./.venv/Scripts/python.exe -m uvicorn app.main:app --reload --port 8000
```

Interactive API docs: http://localhost:8000/docs

```bash
./.venv/Scripts/python.exe -m pytest        # unit + integration
./.venv/Scripts/python.exe -m mypy app
```

## Config

Copy `.env.example` to `.env` and adjust. Nothing is hard-coded (§31) — see
`app/config/settings.py`. `AITO_REQUIRE_API_KEY` is `false` by default for local dev.

**Observability (Phase 12, ADR-012):** `GET /metrics` (Prometheus text format, not gated by
the API key) exposes request counts/latency by mode, token-reduction distribution, semantic-
validation-failure counts, and LLM call counts/latency. Each `/optimize` request also logs one
structured, request-ID-correlated line with per-stage timings (deterministic/structural/llm/
validation) — a lightweight substitute for a full tracing backend, see ADR-012 for why. Any
unexpected exception now returns the standard error envelope instead of a raw traceback.

## Not yet implemented

- A real redundancy signal for `/analyze` (currently always `false`).
- Validator calibration: weights and the 0.85 threshold are untuned heuristics (Phase 13).
- Live-key verification of the OpenAI/Anthropic adapters (tested against mocked transports only).
- Database/Redis (no persistence needed yet — settings are in-memory, usage stats are zeroed).
- `/providers` and `/models` still honestly return empty lists rather than fabricated data.
