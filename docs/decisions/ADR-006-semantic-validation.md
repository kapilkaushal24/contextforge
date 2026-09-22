# ADR-006: Semantic Validation Gate Before Auto-Apply

## Context
Fewer tokens is not "better". An optimization that drops a "not", a number, or a code
block can change what the user asked for while still looking like a fair rewrite. Each
result therefore needs a confidence score, and a low score must stop the prompt being
replaced without review. The validator runs on every request, so it must be fast, free and
must not send prompt text anywhere.

## Decision
- **`ISemanticValidator`** is implemented by `HeuristicSemanticValidator` (deterministic,
  local, no model or network), sharing one feature extractor (`features.py`) with the LLM
  safety gate (`safety.py`) so "what must survive" is defined in one place.
- It returns `semantic_similarity`, `constraint_preservation`, `confidence`, and `issues`
  (stable reason codes such as `missing_numbers`, `missing_negations`,
  `missing_fenced_code`, `introduced_content`).
  - *Constraint preservation* is severity-weighted. Hard (x2): fenced code, numbers,
    identifiers, quoted literals/examples, negations. Soft (x1): constraint words
    (must/at most/...), output-format terms, named entities. New numbers/identifiers/quotes
    introduced by the optimizer are penalized.
  - *Similarity* is a recall-weighted F-score over stemmed content words, ignoring
    politeness and function words, so removing "could you please" or a duplicate sentence
    costs nothing but dropping topic words does.
  - *Confidence* = 0.6 x constraint + 0.4 x similarity, **capped at 0.5 if any hard item is
    lost** — high word overlap can never hide a dropped "not" or number.
- `requires_review = confidence < AITO_SEMANTIC_CONFIDENCE_THRESHOLD` (default 0.85). The API
  returns the scores and `reviewReasons` so the UI can say *why*; the extension must not
  auto-apply a result with `requiresReview: true`.
- Two layers, deliberately: the safety gate decides whether an LLM rewrite may be *accepted*
  at all (binary, conservative); the validator *scores* whatever was accepted.

## Alternatives considered
- **Embedding similarity** — rejected for now: needs a model (latency, size) or a network
  call that exposes prompt text, and cosine similarity is notoriously blind to negation and
  numbers, which is the failure that matters most here.
- **LLM-as-judge** — rejected as the default: costs money on every request, sends the prompt
  to a third party, and is itself a prompt-injection target. It remains a possible opt-in
  second opinion behind the same interface.
- **Pure word overlap (the Phase 5 placeholder)** — rejected: it flagged harmless wrapper
  removal and missed a dropped "not".

## Consequences
- The validator measures whether meaning-bearing tokens survived; it cannot detect a
  rewrite that keeps every token but changes their relationship. Treat the score as a
  safety net, not a proof.
- Scores are heuristic and the weights/threshold are untuned. Calibrate them against the
  Phase 13 benchmark before advertising the numbers to users.
- English-centric (stopwords, stemming, negation words); other languages fall back to a
  weaker signal.
- An optional LLM/embedding validator can be added later as another `ISemanticValidator`.
