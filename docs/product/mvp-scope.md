# MVP Scope & Roadmap

## MVP (Phase 1 shippable product)

1. Chrome Manifest V3 extension shell (React + TS + Vite).
2. Two platform adapters: ChatGPT and Claude (validates the adapter pattern with real DOM
   diversity before adding more).
3. FastAPI backend with `/optimize`, `/analyze`, `/estimate-tokens` implemented.
4. Token estimation via `ITokenizer` (OpenAI + Anthropic + generic fallback).
5. Deterministic optimization (Strategy A: dedup, whitespace, boilerplate) — no LLM call.
6. Structural optimization (Strategy B) — rule/template based, no LLM call.
7. Basic LLM-assisted semantic compression (Strategy F) behind the Model Router, only invoked
   when deterministic/structural savings are insufficient and cost-benefit passes.
8. Before/after preview UI with Apply/Reject/Undo — no silent auto-apply.
9. Token savings calculation and popup dashboard (today's stats only, no historical charts yet).
10. Privacy-first processing: no raw prompt persistence by default.
11. Authentication-ready architecture (API key auth wired, though single-user in MVP).
12. Unit tests for tokenizers, deterministic optimizer, and semantic validator; integration
    test for extension↔backend happy path.
13. Docker Compose for local dev (API + Postgres + Redis).
14. Basic observability: structured logs + request correlation IDs; metrics wiring stubbed.

Explicitly deferred past MVP: Gemini/generic adapters, code-mode optimizer, context-mode
optimizer, enterprise policies/RBAC/SSO, historical analytics, local model inference, feedback
loop-driven strategy tuning.

## Cost-optimization rule (applies from MVP onward)

Before invoking `CloudLLMOptimizer`, the pipeline computes:

```
if estimated_optimization_cost >= estimated_token_savings_value:
    return deterministic/structural result only  # skip the LLM call
```

Both sides configurable per environment; default assumes conservative pricing estimates.

## Definition of done (per MVP feature)

Implemented, tested (unit + relevant integration), error-handled, minimally logged, documented,
config externalized, runs locally, containerizable. (Full checklist:
[master prompt §48](../../README.md).)

## Future roadmap (post-MVP, roughly ordered)

1. Gemini + generic adapter; code-mode and context-mode optimizers (opt-in).
2. Evaluation framework + benchmark dataset (ml/evaluation).
3. Historical analytics in dashboard; cost trend charts.
4. Local model inference option (ONNX/Ollama) for `LOCAL_ONLY` privacy policy.
5. Enterprise: Organizations/Teams/RBAC, admin dashboard, policy engine, audit log UI.
6. SSO/SCIM, on-prem/private deployment option.
7. Feedback-driven strategy tuning (Phase 4 ML roadmap); fine-tuned small models only if
   justified by eval data (Phase 5).
