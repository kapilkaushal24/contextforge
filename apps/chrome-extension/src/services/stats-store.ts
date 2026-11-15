import { emptyStatsFor, todayDateKey, withAppliedOptimization, type AppliedOptimizationEvent, type TodayStats } from "./stats.js";

/**
 * Thin chrome.storage.local wrapper around stats.ts's pure aggregation — mirrors the
 * settings-store.ts / active-platform-store.ts pattern. `local`, not `sync`: this is
 * per-device usage data, not a preference worth syncing across the user's devices, and
 * local's quota comfortably covers a day's worth of counters.
 */
export const TODAY_STATS_KEY = "aito.todayStats" as const;

export async function getTodayStats(): Promise<TodayStats> {
  const stored = await chrome.storage.local.get(TODAY_STATS_KEY);
  const raw = stored[TODAY_STATS_KEY] as TodayStats | undefined;
  const today = todayDateKey();
  if (!raw || raw.date !== today) return emptyStatsFor(today);
  return raw;
}

/** Called once per user-clicked Apply (content/optimization-widget.ts) — never from a
 * failed or merely-viewed optimization, matching the "explicit Apply only" invariant
 * the widget's own state machine already enforces. */
export async function recordAppliedOptimization(event: AppliedOptimizationEvent): Promise<TodayStats> {
  const stored = await chrome.storage.local.get(TODAY_STATS_KEY);
  const raw = stored[TODAY_STATS_KEY] as TodayStats | undefined;
  const today = todayDateKey();
  const next = withAppliedOptimization(raw ?? emptyStatsFor(today), today, event);
  await chrome.storage.local.set({ [TODAY_STATS_KEY]: next });
  return next;
}
