# ADR-001: Chrome Manifest V3

## Context
Chrome Manifest V2 is deprecated/removed from the Chrome Web Store; any new extension must
target Manifest V3. MV3 changes background execution (service workers instead of persistent
background pages) and restricts remote code execution, which affects how we can call the
backend and inject UI.

## Decision
Build on Manifest V3 from day one: service-worker background script, content scripts scoped to
explicit `host_permissions` per supported AI platform, no remote script execution.

## Alternatives considered
- **Manifest V2** — rejected: being sunset by Chrome, not viable for a new product.
- **Firefox-only WebExtension** — rejected for v1: Chrome/Chromium has the larger AI-tool user
  base overlap; MV3 code is largely portable to Firefox later if needed.

## Consequences
- Background logic must be stateless-friendly (service workers can be killed/restarted); any
  state needed across events goes through `chrome.storage`, not in-memory globals.
- No `eval`/remote script loading — all optimization logic that must run in the browser ships
  in the extension bundle; heavier AI logic stays server-side.
- Permissions must be justified per-platform, reinforcing the platform-adapter architecture
  (see [chrome-extension.md](../architecture/chrome-extension.md)).
