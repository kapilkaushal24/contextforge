import type { ExtensionMessage } from "../types/messages.js";
import { getSettings } from "../services/settings-store.js";
import { optimizePrompt } from "../services/api-client.js";

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
