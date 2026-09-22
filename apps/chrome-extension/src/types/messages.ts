import type { OptimizationMode, OptimizeResult, Platform, PrivacyPolicy } from "@ai-token-optimizer/contracts";

/**
 * Messages passed from content scripts to the background service worker via
 * `chrome.runtime.sendMessage`. Content scripts read settings directly from
 * `chrome.storage.sync` (services/settings-store.ts) — the "storage" permission is
 * extension-wide, so no request/response round trip is needed for that. Only the
 * network call goes through the background worker (services/api-client.ts), since
 * content scripts should never call the network directly.
 */
export type ExtensionMessage =
  | {
      type: "OPTIMIZE_REQUEST";
      payload: { text: string; platform: Platform; mode: OptimizationMode; privacyPolicy: PrivacyPolicy };
    }
  | { type: "OPTIMIZE_RESPONSE"; payload: { ok: true; result: OptimizeResult } | { ok: false; error: string } };
