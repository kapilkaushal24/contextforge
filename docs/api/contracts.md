# API Contract Proposal — `/api/v1`

All endpoints: versioned, Pydantic v2 request/response DTOs (never ORM models directly),
consistent error envelope, `X-Request-ID` correlation header, rate-limited per API key.

## Error envelope (consistent across all endpoints)

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "original_text must not be empty",
    "request_id": "..."
  }
}
```

## POST /api/v1/optimize

Request:
```json
{
  "text": "string, required, max 100_000 chars",
  "platform": "chatgpt | claude | gemini | generic",
  "mode": "conservative | balanced | aggressive | code | context",
  "privacy_policy": "cloud_allowed | local_only",
  "conversation_context": ["optional prior turns, for context mode"]
}
```

Response:
```json
{
  "original_text": "...",
  "optimized_text": "...",
  "original_tokens": 1250,
  "optimized_tokens": 820,
  "tokens_saved": 430,
  "reduction_percentage": 34.4,
  "estimated_cost_saved": 0.012,
  "optimization_mode": "balanced",
  "confidence": 0.96,
  "requires_review": false,
  "changes": [
    { "type": "deduplication", "description": "Removed repeated requirement", "impact": "low" }
  ]
}
```

## POST /api/v1/analyze

Classifies content (code / documentation / conversation / general) and flags redundancy
without producing a full optimized rewrite. Used for the lightweight "1,240 tokens" indicator
before the user opts into full optimization.

## POST /api/v1/estimate-tokens

Request: `{ "text": "...", "provider": "openai | anthropic | gemini | generic" }`
Response: `{ "tokens": 1250, "provider": "openai", "method": "estimated" }`

## POST /api/v1/validate

Given `original_text` + `optimized_text`, returns the semantic validation object described in
[ai-ml.md §6](../architecture/ai-ml.md#6-semantic-validation) without re-running optimization.

## GET /api/v1/providers

Lists configured `IAIProvider` adapters and their availability/status.

## GET /api/v1/models

Lists models per provider with pricing metadata (for cost estimation).

## GET /api/v1/usage

Query params: `range`, `organization_id` (enterprise). Returns aggregated
`OPTIMIZATION_METRIC` rollups — never raw prompt text.

## GET /api/v1/settings / PUT /api/v1/settings

User/org-level settings: default mode, privacy policy, feature flags.

## POST /api/v1/feedback

```json
{ "request_id": "...", "rating": "helpful | not_helpful", "reason": "changed_intent | too_aggressive | other" }
```

Used to inform strategy tuning (Phase 4 of the ML roadmap) — never used for model training
without explicit consent (see product requirements §7).
