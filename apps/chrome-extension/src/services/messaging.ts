import type { OptimizationMode, OptimizeResult, Platform, PrivacyPolicy } from "@ai-token-optimizer/contracts";
import type { ExtensionMessage } from "../types/messages.js";

/**
 * Content-script-side call to the background worker's /optimize proxy. Never throws
 * in a way the caller can't handle gracefully — resolves to a discriminated result so
 * the widget can always fall back to "optimization unavailable" (see error-handling
 * principle, docs/architecture/system-overview.md).
 */
export async function requestOptimization(
  text: string,
  platform: Platform,
  mode: OptimizationMode,
  privacyPolicy: PrivacyPolicy,
): Promise<{ ok: true; result: OptimizeResult } | { ok: false; error: string }> {
  const request: ExtensionMessage = {
    type: "OPTIMIZE_REQUEST",
    payload: { text, platform, mode, privacyPolicy },
  };

  try {
    const response = (await chrome.runtime.sendMessage(request)) as ExtensionMessage | undefined;
    if (response?.type !== "OPTIMIZE_RESPONSE") {
      return { ok: false, error: "No response from the extension background worker" };
    }
    return response.payload;
  } catch (error) {
    const message = error instanceof Error ? error.message : "Extension messaging failed";
    return { ok: false, error: message };
  }
}
