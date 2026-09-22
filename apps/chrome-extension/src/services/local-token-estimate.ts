/**
 * Rough, purely local token estimate shown in the widget before the user clicks
 * Optimize — so the indicator costs zero latency and no network call (§38 performance
 * principle: minimal extension overhead). This is display-only and always labeled
 * "~"; the authoritative count comes back from POST /api/v1/optimize.
 */
export function estimateTokensLocally(text: string): number {
  const trimmed = text.trim();
  if (trimmed === "") return 0;
  return Math.max(1, Math.ceil(trimmed.length / 4));
}
