import type { OptimizationMode, OptimizeResult, Platform } from "@ai-token-optimizer/contracts";

/**
 * Messages passed between content scripts and the background service worker via
 * `chrome.runtime.sendMessage`. A discriminated union keeps handlers exhaustive.
 */
export type ExtensionMessage =
  | { type: "OPTIMIZE_REQUEST"; payload: { text: string; platform: Platform; mode: OptimizationMode } }
  | { type: "OPTIMIZE_RESPONSE"; payload: { ok: true; result: OptimizeResult } | { ok: false; error: string } }
  | { type: "GET_SETTINGS_REQUEST" }
  | { type: "GET_SETTINGS_RESPONSE"; payload: { defaultMode: OptimizationMode } };
