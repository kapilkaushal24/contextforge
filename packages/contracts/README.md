# @ai-token-optimizer/contracts

Shared TypeScript types for the `/api/v1/*` request/response shapes described in
[docs/api/contracts.md](../../docs/api/contracts.md). This is the source of truth the Chrome
extension imports; the Python backend's Pydantic DTOs (added in Phase 5) are hand-kept in sync
with these shapes at the API boundary.

```bash
npm run build      # emits dist/ (.js + .d.ts)
npm run typecheck
```
