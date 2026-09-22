# ADR-003: Tokenizer Abstraction (`ITokenizer` per provider)

## Context
Providers tokenize differently, and only some publish an offline tokenizer. The product
shows before/after token counts and cost savings, so counts must be provider-appropriate
without the optimizer or API knowing which provider is in play, and must never be
presented as billed actuals.

## Decision
- `ITokenizer` (a `Protocol` in `optimization-core`) is the only counting interface.
  Implementations live in `packages/tokenizers`: `OpenAITokenizer` (tiktoken `o200k_base`),
  and `HeuristicTokenizer` for Anthropic, Gemini and generic.
- `HeuristicTokenizer` counts word and punctuation chunks (not flat chars/4) so code-heavy
  text is not under-counted; Anthropic uses a slightly denser calibration (3.5 chars/token).
- tiktoken is an optional extra. If it or its encoding data is unavailable (e.g. offline),
  `OpenAITokenizer` falls back to the heuristic rather than failing the request.
- `TokenizerRegistry.get(provider)` resolves an implementation and falls back to GENERIC.
- The platform→tokenizer mapping is configuration (`AITO_PLATFORM_TOKENIZER_MAP`), not code,
  consistent with ADR-009 (platform ids are open strings; unmapped → generic).
- The API always reports `method: "estimated"`. `provider_reported` is reserved for real
  usage data from a provider and is never produced locally.
- Cost is `tokens_saved / 1000 * AITO_INPUT_PRICE_PER_1K_USD` — a configurable estimate.

## Alternatives considered
- **Hard-code one tokenizer (chars/4 or tiktoken) for everything** — rejected: inaccurate for
  non-OpenAI providers and impossible to swap per provider.
- **Bundle a price table per model** — rejected: prices change frequently and a stale table
  would silently misreport savings; a single configured price is honest and simple.
- **Call provider token-count APIs** — rejected for the hot path: adds latency, cost and a
  privacy exposure (prompt text leaves the service just to be counted).

## Consequences
- Anthropic and Gemini counts are approximations; the UI must keep the "estimated" label.
- Exact OpenAI counts depend on tiktoken being installed and its encoding being cached.
- Adding a provider means one new `ITokenizer` and one registry entry.
