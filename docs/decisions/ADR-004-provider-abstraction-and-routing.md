# ADR-004: AI Provider Abstraction and Model Router

## Context
Semantic compression needs an LLM, but the optimizer must not depend on one vendor, must
respect privacy policy, must never cost more than it saves, and must treat both the user's
prompt and the model's reply as untrusted.

## Decision
- **`IAIProvider`** (`Protocol` in `optimization-core`): `complete(*, system, user, max_tokens)`.
  Trusted instructions and untrusted content are separate arguments, mapped to separate
  provider roles (OpenAI `system`/`user` messages; Anthropic top-level `system` + `user`).
  Adapters (`packages/provider-adapters`) use fixed base URLs (no SSRF surface) and raise
  `ProviderError` with messages that never contain prompt text or credentials.
- **Async strategies:** `IOptimizationStrategy.optimize` is `async` so the LLM strategy and
  local strategies share one interface.
- **Trust boundary:** the system prompt states the tagged text is data, never instructions;
  literal `<user_prompt>` tags inside user text are neutralized.
- **Output is untrusted:** a rewrite replaces the prompt only if it passes a deterministic
  gate (`safety.py`): fenced code verbatim, all numbers, identifiers and negations kept, and
  strictly shorter. Otherwise the original text is kept. (Full semantic validation: Phase 9.)
- **`ModelRouter.route(...) -> RoutingDecision(strategy | None, reason)`** applies gates in
  order: configured → enabled → privacy not `local_only` → mode/type allows (never code, never
  conservative) → cost gate (estimated optimizer cost < estimated downstream savings).
  Reasons are stable codes and are logged; prompt text never is.
- **Off by default:** `AITO_ENABLE_LLM_OPTIMIZATION=false`; needs a configured key.
- **Failure policy:** any `ProviderError` falls back to the deterministic/structural result.

## Alternatives considered
- **Let the LLM run whenever configured** — rejected: violates "cheapest safe transformation
  first" and can cost more than it saves on short prompts.
- **Single combined prompt string** — rejected: no role separation, weaker injection defense.
- **Trust the model's output** — rejected: an LLM can drop a "not" or a number while sounding fine.

## Consequences
- The cost gate uses planning ratios (expected 25% reduction), not measured ones; tune with
  the Phase 13 evaluation harness.
- The safety gate is intentionally conservative and will reject some valid rewrites.
- Local inference (ADR-007) remains future work; a local provider is just another `IAIProvider`.
- Adapters are tested against mocked transports; live-API behavior needs a real key to verify.
