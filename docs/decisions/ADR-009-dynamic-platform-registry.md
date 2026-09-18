# ADR-009: Dynamic Platform Registry + Tab-Based Auto-Detection

## Context
The initial extension scaffold (Phase 4) modeled "which AI platform" as a closed set —
a TypeScript union type (`"chatgpt" | "claude" | "gemini" | "generic"`) mirrored by a Python
enum on the backend, with the matching URL regexes duplicated across the manifest config and
each adapter's `matches()` method. Every new platform meant editing multiple files and widening
a type used throughout the codebase. It also gave the extension no way to know which platform
the user is currently on without asking each adapter to re-check the URL.

## Decision
1. Replace the closed `Platform` union/enum with an open `string` on both sides
   (`packages/contracts/src/enums.ts`, `packages/optimization-core/src/optimization_core/enums.py`).
   Nothing outside the extension's own platform registry decides what a valid platform id is.
2. Introduce a single registry, `apps/chrome-extension/src/constants/platforms.ts`
   (`PLATFORM_REGISTRY` + `detectPlatform(url)`), as the only place platform URL patterns are
   defined. It feeds:
   - `manifest.config.ts` — `content_scripts.matches` / `host_permissions` are derived via
     `allOriginPatterns()`, not hand-copied.
   - Each adapter's `matches()` — delegates to `detectPlatform(url)?.id === this.id`.
3. Add tab-based auto-detection in the background service worker: `chrome.tabs.onActivated`
   and `chrome.tabs.onUpdated` listeners resolve the active tab's URL against the registry and
   cache the result in `chrome.storage.session` (`active-platform-store.ts`), so "which platform
   is the user on right now" is tracked continuously, not re-derived ad hoc.
4. The popup subscribes via `useActivePlatform()`, which live-queries `chrome.tabs` on open
   (most accurate at that instant) and re-resolves on `chrome.storage.onChanged`, so it stays
   correct if the user switches tabs while the popup happens to be open.

## Alternatives considered
- **Keep the closed union, add more values as platforms are added** — rejected: this is exactly
  the maintenance burden being removed; every new platform would still touch contracts, the
  Python enum, the manifest, and an adapter.
- **Detect the platform only inside the content script (no background tracking)** — rejected:
  the content script only knows about the tab it's injected into; the popup (a separate
  execution context) would have no way to know "what tab is active right now" without either
  polling or a shared state channel. The background worker is the natural owner of
  cross-tab state.
- **Poll `chrome.tabs.query` from the popup only, no background listener** — considered and
  partially kept (the popup still does a live query first, for accuracy) but rejected as the
  *sole* mechanism: it can't react while the popup is closed, and gives future consumers
  (e.g. a content-script badge) nothing to read.

## Consequences
- Adding a new AI platform is now: add one entry to `PLATFORM_REGISTRY`, write its adapter. No
  other file changes, no type to widen.
- `Platform` being a plain `string` in the contracts means the backend can no longer rely on
  the type system to enumerate valid platforms; any platform-specific backend behavior (e.g.
  a specialized tokenizer) must handle unknown ids gracefully and fall back to the generic
  path — this is already the documented default (`GenericTokenizer` fallback, `ai-ml.md`).
- Tab tracking uses `chrome.storage.session` (in-memory, cleared on browser restart) rather
  than `chrome.storage.sync`/`local` — this is derived, ephemeral state, never something to
  persist or sync across devices.
- No new permission was required: `host_permissions` already covers the registered platform
  origins, which is what lets the background listeners read `tab.url` without the broader
  `tabs` permission (ADR-001's minimum-permissions principle holds).
