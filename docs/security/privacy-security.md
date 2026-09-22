# Security & Privacy Architecture

## 1. Privacy-first defaults

- Default flow: `Prompt -> Process -> Return result -> Discard raw content`. Raw prompt text
  is **not** persisted by default; only derived metrics (token counts, reduction %, mode used,
  timestamp, platform id) are stored, tied to a user/org id.
- Raw prompt storage is opt-in only (per-user or org policy), and when enabled, sensitive
  fields are encrypted at rest (column-level encryption or a dedicated encrypted store).
- Cloud vs. local optimization is a configurable policy (`PrivacyPolicy.LOCAL_ONLY` routes
  never leave the browser/backend boundary; see Model Router in
  [ai-ml.md](../architecture/ai-ml.md)).
- PII/sensitive-data detection runs before any cloud LLM call; matches can block cloud routing
  per policy. Implemented (Phase 11, ADR-011): `optimization_core.pii.detect_pii` (local,
  deterministic — email, phone, SSN, credit card, API key) feeds `ModelRouter`'s
  `contains_sensitive_content` gate, controlled by `RouterPolicy.block_pii_from_cloud`
  (`AITO_BLOCK_PII_FROM_CLOUD`, default on). Detected categories are reported in the API
  response (`sensitiveContentCategories`) — never the matched text.

## 2. Transport & storage security

- TLS everywhere (extension ↔ API, API ↔ providers).
- Secrets (DB credentials, provider API keys, JWT signing keys) never hard-coded — `.env` in
  dev, a secrets manager (AWS Secrets Manager / Azure Key Vault / GCP Secret Manager) in prod.
- Postgres: encryption at rest via managed instance; Redis: no sensitive prompt content cached
  without explicit justification and TTL.

## 3. AuthN/AuthZ

- API keys for extension→backend initially; architecture leaves room for OAuth2/OIDC + JWT for
  multi-user/enterprise (SSO/SCIM in enterprise phase).
- RBAC model reserved for org/team/roles (see [database ERD](../architecture/database-erd.md)).

## 4. Prompt injection defense

Four-zone trust boundary (system instructions / optimizer policy / user content / external
context) enforced at the optimizer core — detailed in
[ai-ml.md §7](../architecture/ai-ml.md#7-prompt-injection-boundary). User/external content is
always treated as data to transform, never as instructions to the optimizer, the provider
client, or any tool-calling logic. A hijacked/compromised provider's *output* is equally
untrusted: `optimization_core.safety.missing_critical_content` rejects a rewrite that is
either missing critical content or off-topic (`topic_drift`) relative to the original, and
`HeuristicSemanticValidator` scores an off-topic result as low-confidence for the same
reason — see ADR-011 for the specific gap a battery of injection payloads found and fixed,
and `tests/security/test_prompt_injection_api.py` / `optimization-core`'s
`tests/test_prompt_injection.py` for the regression coverage.

## 5. Application security controls

| Concern | Control |
|---|---|
| Input validation | Pydantic v2 models on every API boundary, max payload size |
| Output validation | Schema-validated responses only, no raw model output passthrough |
| XSS | Extension renders optimizer output as text, never `innerHTML`; CSP in manifest |
| CSRF | API is token-authenticated, not cookie-session based |
| SSRF | Provider calls go through an allow-listed adapter list, no user-controlled URLs |
| Rate limiting | Per API key, enforced at gateway |
| CORS | Restricted to the extension's origin |
| Extension permissions | Minimum necessary, no `<all_urls>` (see chrome-extension.md §5) |

## 6. Data classification (for future enterprise policy engine)

- **Public**: aggregate anonymized metrics.
- **Internal**: org-level usage analytics.
- **Confidential**: raw prompt text (opt-in only), API keys, auth tokens.
- **Restricted**: detected PII/secrets inside prompts — never sent to cloud providers unless
  explicitly permitted by org policy.

## 7. Audit logging (enterprise extension point)

`AuditLog` entity (see ERD) records policy-relevant events (optimization requests, policy
changes, admin actions) without storing raw prompt content unless raw-prompt-storage is
explicitly enabled.
