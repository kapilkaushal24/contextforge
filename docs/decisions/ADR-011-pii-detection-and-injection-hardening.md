# ADR-011: PII Detection Gate + Prompt-Injection Hardening (Phase 11)

## Context
Two gaps from docs/security/privacy-security.md §1 ("PII/sensitive-data detection runs
before any cloud LLM call") and the ADR-004 trust boundary were unimplemented or
untested until Phase 11: (1) nothing actually detected sensitive content before routing
to a cloud LLM, and (2) the prompt-injection defense built in Phase 8 had never been
stress-tested with a battery of real injection payloads.

Writing that stress-test suite immediately found two real defects, not just gaps in
test coverage:
- **Safety gate** (`safety.py`, gates LLM output before it may replace the prompt): a
  payload with no numbers/identifiers/quotes/negations to lose (e.g. "Ignore all
  instructions...") let a completely unrelated short reply ("PWNED") through, because
  the gate only checked for *lost* hard content, never *topical relevance*.
- **Semantic validator** (`validator.py`, scores whatever was accepted): the same class
  of prompt scored `constraint_preservation = 1.0` (nothing to lose) and
  `confidence = 0.6` for an unrelated one-word reply — high enough to not obviously
  need review.

## Decision
**PII detection** (`optimization_core/pii.py`, `detect_pii`): local, deterministic,
regex + Luhn-checksum detection for email, phone (requires a separator — see the
module's precision-tradeoff note), SSN (US format), credit card, and API keys
(OpenAI/Stripe, GitHub, Slack, AWS, Google prefixes). No model, no network, categories
only ever logged/returned — never the matched text.

**Router gate**: `ModelRouter.route` gains `contains_sensitive_content` (keyword-only,
default `False`) and `RouterPolicy.block_pii_from_cloud` (default `True`). Detected
sensitive content blocks cloud LLM routing regardless of `privacy_policy`, unless an
operator explicitly disables the policy flag. `OptimizationResult` and the API's
`OptimizeResult` gain `sensitive_categories` / `sensitiveContentCategories` — reported
whenever found, independent of whether the LLM step was even reached, for transparency.

**Safety gate fix**: added a `topic_drift` check — when the original has enough content
words to compare (>= 3) and stemmed-content-word overlap with the candidate falls below
30%, the rewrite is rejected regardless of what hard-content categories were or weren't
present to lose.

**Validator fix**: the same signal, applied to confidence instead of a binary
accept/reject — similarity below 20% (with the same >= 3 content-word floor) caps
confidence at 0.3 and adds a `topic_drift` issue, so a hijacked or off-topic "rewrite"
that slipped past the safety gate (or was validated independently via `/validate`) still
reads as low-confidence rather than a deceptive 0.6.

**Test suite**: `packages/optimization-core/tests/test_prompt_injection.py` (payload
battery against the strategy directly) and
`services/optimization-service/tests/security/` (API-key auth, payload-limit boundary
conditions, PII-blocks-routing, and the same injection battery through the live
`/api/v1/optimize` and `/api/v1/validate` endpoints).

## Alternatives considered
- **PII detection via an LLM/NER model** — rejected: adds latency and cost to every
  request, and would itself send the prompt to a model before the privacy decision
  about sending it to a model has even been made.
- **Only fix the validator, not the safety gate** — rejected: the safety gate is what
  actually decides whether a hijacked rewrite reaches the user at all; fixing only the
  score without fixing the gate leaves the door open, just with a truthful label on it.
- **Block on any detected PII regardless of policy** — rejected: `block_pii_from_cloud`
  stays a policy flag (defaulting on) rather than a hard-coded rule, consistent with
  ADR-004's "policy, not hardcoded" theme; an enterprise deployment might have its own
  compliance review process that accepts this differently.

## Consequences
- `topic_drift` in both safety.py and validator.py duplicates the same threshold-and-cap
  shape rather than sharing one implementation — they operate on different data (a
  boolean gate vs. a continuous score) and duplicating a ~5-line check was judged
  clearer than a shared abstraction for two call sites with different semantics.
- Phone-number detection intentionally misses unseparated digit runs (precision over
  recall) — see `pii.py`'s docstring.
- `detect_pii` runs on every `/optimize` request regardless of whether cloud LLM
  optimization is even enabled, so the categories are always available for the UI —
  this is a few regex passes over the prompt, not a meaningful cost.
