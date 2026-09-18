import type { ExtensionMessage } from "../types/messages.js";
import { getSettings } from "../services/settings-store.js";
import { optimizePrompt } from "../services/api-client.js";
import { setActivePlatform } from "../services/active-platform-store.js";

/**
 * MV3 background service worker. Stateless between events by design — any state
 * needed across invocations goes through chrome.storage, never module-level
 * variables (ADR-001: service workers can be killed/restarted at any time).
 */
chrome.runtime.onMessage.addListener((message: ExtensionMessage, _sender, sendResponse) => {
  switch (message.type) {
    case "OPTIMIZE_REQUEST": {
      optimizePrompt({
        text: message.payload.text,
        platform: message.payload.platform,
        mode: message.payload.mode,
        privacyPolicy: "cloud_allowed",
      })
        .then((result) => {
          sendResponse({ type: "OPTIMIZE_RESPONSE", payload: { ok: true, result } } satisfies ExtensionMessage);
        })
        .catch((error: unknown) => {
          // Never block the user's workflow on a backend failure — the caller falls
          // back to the original prompt (see error-handling principle).
          const messageText = error instanceof Error ? error.message : "Optimization unavailable";
          sendResponse({
            type: "OPTIMIZE_RESPONSE",
            payload: { ok: false, error: messageText },
          } satisfies ExtensionMessage);
        });
      return true; // keep the message channel open for the async sendResponse above
    }

    case "GET_SETTINGS_REQUEST": {
      getSettings().then((settings) => {
        sendResponse({
          type: "GET_SETTINGS_RESPONSE",
          payload: { defaultMode: settings.defaultMode },
        } satisfies ExtensionMessage);
      });
      return true;
    }

    default:
      return false;
  }
});

/**
 * Auto-detects the active AI platform whenever the user switches tabs or a tab
 * finishes navigating (ADR-009). No platform id is hardcoded here — detection is
 * entirely driven by the registry in constants/platforms.ts, so supporting a new
 * platform never requires touching this file.
 */
async function handleTabChange(tab: chrome.tabs.Tab | undefined): Promise<void> {
  if (!tab) return;
  await setActivePlatform(tab);
}

chrome.tabs.onActivated.addListener(({ tabId }) => {
  void chrome.tabs.get(tabId).then(handleTabChange).catch(() => {
    // Tab may have closed between the event firing and this lookup — safe to ignore.
  });
});

chrome.tabs.onUpdated.addListener((_tabId, changeInfo, tab) => {
  if (changeInfo.status === "complete") {
    void handleTabChange(tab);
  }
});

// Populate immediately on service-worker startup so the popup has data before the
// first tab switch/navigation event fires.
chrome.tabs
  .query({ active: true, lastFocusedWindow: true })
  .then(([tab]) => handleTabChange(tab))
  .catch(() => {
    // No focused window yet (e.g. extension just installed) — safe to ignore.
  });
