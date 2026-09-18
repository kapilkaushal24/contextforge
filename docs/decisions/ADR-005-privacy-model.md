# ADR-005: Privacy Model — No Raw-Prompt Persistence by Default

## Context
The extension processes potentially sensitive user prompts (proprietary code, business
context, PII). Storing this data by default creates compliance risk and erodes user trust,
which is core to product adoption per the product requirements' privacy-first principle.

## Decision
Default data flow is `Prompt -> Process -> Return result -> Discard`. Raw prompt text is never
persisted unless a user or org explicitly opts in via policy; when opted in, it is stored
encrypted with configurable retention. Only derived, non-reversible metrics (token counts,
percentages, mode, timestamps) are stored by default. See
[privacy-security.md](../security/privacy-security.md) and the ERD's
`OPTIMIZATION_REQUEST.raw_text_stored` flag.

## Alternatives considered
- **Store everything by default for analytics/debugging convenience** — rejected: highest
  privacy risk, conflicts with the product's core trust proposition, and complicates
  compliance for enterprise adoption.
- **Store nothing, ever (even opt-in)** — rejected: blocks legitimate enterprise use cases
  (audit requirements, debugging optimization quality) that need raw-text access under
  explicit consent.

## Consequences
- Debugging optimization quality issues without stored raw text requires either user-supplied
  reproduction or opt-in logging — slower incident response by design, traded for privacy.
- Analytics/dashboards must be built entirely on the pre-aggregated `OPTIMIZATION_METRIC`
  rollup table, not on scanning raw request text.
- Any future feature that wants raw text (e.g., training data collection) requires an explicit,
  separate consent flow — it cannot piggyback on existing stored data.
