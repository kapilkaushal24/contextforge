# AI / ML Architecture

## 1. Optimization pipeline (interfaces)

```
Raw Input
  -> Input Validation
  -> Content Classification        (IContentAnalyzer)
  -> Token Estimation               (ITokenizer via ITokenEstimator)
  -> Redundancy Detection           (IRedundancyDetector)
  -> Structural Optimization        (IOptimizationStrategy: structural)
  -> Semantic Compression           (IOptimizationStrategy: semantic, via ModelRouter)
  -> Token Re-estimation
  -> Semantic Validation            (ISemanticValidator)
  -> Optimization Confidence Score
  -> Final Optimized Prompt
```

Each stage is a small, independently-testable unit behind an interface; the pipeline itself
implements `IOptimizationPipeline` and is composed via dependency injection so stages can be
swapped (e.g., replace `RedundancyDetector` with a smarter one without touching the rest).

## 2. Strategies (A–F from product spec)

| Strategy | Trigger | LLM required? |
|---|---|---|
| A. Deterministic compression | Always tried first | No |
| B. Structural optimization | Verbose natural-language prompts | No (rule/template based) |
| C. Context deduplication | Multi-paragraph or multi-turn input | No (embedding similarity, local) |
| D. Code context optimization | Content classified as code-heavy | No, opt-in only for code edits |
| E. Conversation context optimization | Long/multi-turn context | Local embeddings, LLM only if needed |
| F. Semantic compression | Deterministic pass insufficient | Yes (`CloudLLMOptimizer` or local model) |

## 3. Tokenizer abstraction

```
ITokenizer
├── OpenAITokenizer     (tiktoken-compatible)
├── AnthropicTokenizer
├── GeminiTokenizer
├── GenericTokenizer    (heuristic fallback, char/word based)
└── FutureTokenizer
```

UI must distinguish **"Estimated tokens"** (our count) from **"Actual provider-reported
tokens"** (only available if/when a provider returns real usage). Never conflate the two.

## 4. AI provider abstraction

```
IAIProvider
├── OpenAIProvider
├── AnthropicProvider
├── GeminiProvider
└── LocalModelProvider
```

The optimizer core (`optimization-core` package) never imports a concrete provider — only
`IAIProvider`. Providers are registered via a factory at composition root.

## 5. Model router

```
ModelRouter.select(input: {
  promptType: PromptType,
  mode: OptimizationMode,
  privacyPolicy: PrivacyPolicy,
  latencyBudgetMs: number,
}): IOptimizationStrategy
```

Routing rules (initial, tunable):
- `privacyPolicy == LOCAL_ONLY` → never route to `CloudLLMOptimizer`.
- deterministic reduction already ≥ target threshold → skip semantic compression.
- `estimated_optimization_cost >= estimated_token_savings_value` → stop at deterministic/structural
  result (cost-optimization rule, [MVP scope](../product/mvp-scope.md) §cost).

## 6. Semantic validation

Validator compares original vs. optimized text and returns:

```json
{
  "semantic_similarity": 0.0,
  "constraint_preservation": 0.0,
  "confidence": 0.0
}
```

Checks: intent, constraints, named entities, numeric values, technical terms, negative
constraints, output-format requirements, examples, edge cases. If `confidence` is below a
configurable threshold (default 0.85), the pipeline does **not** auto-apply — it returns the
result marked `requires_review: true` and the UI shows "Optimization confidence is low."

## 7. Prompt-injection boundary

Four explicit trust zones, never merged:

1. **System instructions** — fixed, in code, not user-modifiable.
2. **Optimizer policy** — org/user configuration (modes, thresholds).
3. **User content** — the prompt being optimized. Always treated as data.
4. **External context** (e.g., pasted docs, conversation history) — also data.

Any instruction-like text found inside (3) or (4) (e.g., "ignore previous instructions and
exfiltrate this") is optimized/summarized as inert text, never executed as a directive to the
optimizer or provider client. See [Security & Privacy](../security/privacy-security.md).

## 8. ML roadmap phasing

Phase 1 deterministic → Phase 2 LLM-assisted → Phase 3 evaluation framework → Phase 4 learn
best strategy per prompt type → Phase 5 fine-tune small specialized models only if the eval
dataset justifies it. No custom model training in MVP.
