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
  setText(text: string): void;
  onSubmitIntercept(cb: (text: string) => Promise<string>): void; // returns text to actually submit
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

## 4. Messaging flow

Content script → `chrome.runtime.sendMessage` → background service worker → backend API →
response relayed back to content script → rendered in an injected preview UI (shadow DOM to
avoid CSS collisions with the host page).

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
