import type { ApiErrorBody, OptimizeRequest, OptimizeResult } from "@ai-token-optimizer/contracts";
import { ApiError } from "@ai-token-optimizer/contracts";
import { API_ENDPOINTS } from "../constants/api.js";

/**
 * Thin fetch wrapper around the optimization backend. Lives in the background
 * service worker (content scripts should never call the network directly) so all
 * outbound requests go through one auditable choke point.
 *
 * Per the error-handling principle (system-overview.md), a failed call must never
 * throw in a way that blocks the caller's workflow — callers are expected to fall
 * back to the original, unoptimized prompt.
 */
export async function optimizePrompt(request: OptimizeRequest, signal?: AbortSignal): Promise<OptimizeResult> {
  const response = await fetch(API_ENDPOINTS.optimize, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request),
    signal,
  });

  if (!response.ok) {
    const body = (await response.json().catch(() => null)) as ApiErrorBody | null;
    if (body) throw new ApiError(body);
    throw new Error(`Optimization request failed with status ${response.status}`);
  }

  return (await response.json()) as OptimizeResult;
}
