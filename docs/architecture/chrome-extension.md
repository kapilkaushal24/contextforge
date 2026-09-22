# Chrome Extension Architecture

## 1. Stack

Manifest V3, TypeScript (strict), React, Vite, Tailwind, Chrome Storage/Runtime Messaging APIs.

## 2. Folder layout (`apps/chrome-extension/src`)

```
background/       service worker: API calls, auth token storage, cross-tab coordination
content/          content scripts injected into supported AI sites
popup/            popup dashboard UI (React)
options/          settings page UI (React)
components/       shared React components (diff view, token badge, mode selector)
services/         API client, messaging bus, token estimator (local fallback)
adapters/         IPlatformAdapter implementations (ChatGPT, Claude, Gemini, Generic)
hooks/            React hooks (useOptimization, useSettings, useStats)
store/            extension-local state (Zustand or Context — decide in ADR-001-followup)
types/            shared TypeScript types/interfaces
constants/        selector constants, API endpoints, feature flag keys
assets/           icons, static assets
```

## 3. Platform adapter pattern

```ts
interface IPlatformAdapter {
  id: string;                              // 'chatgpt' | 'claude' | 'gemini' | 'generic'
  matches(url: string): boolean;
  getInputElement(): HTMLElement | null;
  getCurrentText(): string;
  setText(text: string): void;             // only ever called from an Apply/Undo click — see §3b/ADR-010
  extractConversationContext?(): string[];  // optional, for context-mode optimization
}
```

`PlatformAdapterFactory` selects the adapter by URL match. All DOM selectors live inside a
single adapter file per platform (`adapters/chatgpt.adapter.ts`, etc.) and nowhere else — if a
site changes its DOM, only that file changes. Selectors are centralized as named constants
(`constants/selectors.ts`) so they can be versioned and updated without touching adapter logic.

`id` is a plain `string`, not a closed enum — see §3a.

## 3a. Platform registry & auto-detection (ADR-009)

"Which AI platform" is data, not a type. `constants/platforms.ts` exports a single
`PLATFORM_REGISTRY` (id, display name, URL patterns, manifest origin patterns) and a
`detectPlatform(url)` helper — the **only** place a platform's URL patterns are defined.
Everything else derives from it:

- `manifest.config.ts` builds `content_scripts.matches` / `host_permissions` from
  `allOriginPatterns()` instead of hand-copied literals.
- Each adapter's `matches()` delegates to `detectPlatform(url)?.id === this.id`.
- The background service worker listens to `chrome.tabs.onActivated` /
  `chrome.tabs.onUpdated` and writes the detected platform for the active tab to
  `chrome.storage.session` (`services/active-platform-store.ts`) on every tab switch or
  completed navigation — so "what platform is the user on" is tracked continuously.
- The popup's `useActivePlatform()` hook live-queries `chrome.tabs` on open and re-resolves on
  `chrome.storage.onChanged`, showing a `PlatformBadge` ("Detected: ChatGPT" /
  "Not on a supported AI site").

Adding a platform is: one entry in `PLATFORM_REGISTRY` + one adapter file. No enum to widen, no
manifest edit, no backend change (the `Platform` field in the API contract is an open string).

## 3b. Proactive optimization widget (ADR-010)

There is no submit interception — nothing hooks the platform's Send button. Instead:

- `content/optimization-widget.ts` watches the adapter's input element (debounced 400ms) and
  drives a pure state machine, `content/optimization-widget-state.ts`
  (`hidden → idle → loading → result → applied`, plus `error`), unit-tested independently of
  the DOM.
- **idle**: once the prompt reaches `MIN_WORDS_TO_SHOW` (8) words, a small shadow-DOM pill shows
  a local, zero-latency `~N tokens` estimate (`services/local-token-estimate.ts`) and an
  **Optimize** button — the only thing that calls the backend.
- **result**: shows before/after token counts, reduction %, a review warning (human-readable
  reasons via `constants/review-reasons.ts`, never the raw API codes) when `requiresReview` is
  true, the changes made, and the optimized text — with **Apply** and **Keep original** buttons.
- **applied**: `adapter.setText()` is called — the *only* place that happens — and an **Undo**
  restores the pre-optimization text via the same call. This is the invariant the state machine
  exists to enforce; see its file-level comment.
- **error**: a non-blocking "optimization unavailable" pill, auto-dismissed after 6s; the input
  is never touched.
- The widget is rendered inside a closed shadow root (`content/panel.ts`) so host-page CSS can
  neither affect it nor be affected by it, and all user/API-derived text goes through
  `textContent`/DOM construction (`content/dom.ts`) — never `innerHTML`.

## 4. Messaging flow

Content script → `chrome.runtime.sendMessage` (`OPTIMIZE_REQUEST`, mode/privacy read from
`chrome.storage.sync` directly in the content script) → background service worker → backend API
→ `OPTIMIZE_RESPONSE` relayed back → rendered by the widget above.

## 5. Permissions (minimum necessary)

- `storage` — settings, cached stats.
- `activeTab` + narrowly scoped `host_permissions` per supported platform (not `<all_urls>`).
- No `webRequest`, no `tabs` beyond what's required, no broad content injection.
- Backend API host added to `host_permissions` explicitly.

## 6. UX contract

- Optimization is **never** auto-applied by default; user must click Apply.
- A visible Undo restores the pre-optimization text for at least the current session.
- If the backend is unreachable or fails, the original prompt is left untouched and a
  non-blocking "optimization unavailable" indicator is shown (see error-handling principle
  in system-overview.md).
