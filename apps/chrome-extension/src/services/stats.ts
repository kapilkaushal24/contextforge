/**
 * Pure "Today" stats aggregation — kept side-effect-free and framework-free so it's
 * unit-testable without chrome.storage (see stats.test.ts); stats-store.ts is the thin
 * chrome.storage.local wrapper around this, mirroring the settings-store.ts /
 * active-platform-store.ts split already used elsewhere in this codebase.
 */

export interface TodayStats {
  /** Local YYYY-MM-DD the counters below belong to — a stats object from a previous
   * day is stale and must be treated as empty, never carried forward. */
  date: string;
  promptsOptimized: number;
  tokensSaved: number;
  /** Sum of each applied optimization's reductionPercentage, not an average — the
   * average is derived (see averageReduction) so it never needs its own reset logic. */
  reductionPercentageSum: number;
}

export function todayDateKey(now: Date = new Date()): string {
  const year = now.getFullYear();
  const month = String(now.getMonth() + 1).padStart(2, "0");
  const day = String(now.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

export function emptyStatsFor(date: string): TodayStats {
  return { date, promptsOptimized: 0, tokensSaved: 0, reductionPercentageSum: 0 };
}

export interface AppliedOptimizationEvent {
  tokensSaved: number;
  reductionPercentage: number;
}

/** Folds one applied-optimization event into the running "Today" totals. If `current`
 * belongs to an earlier day than `today`, it's discarded (day rollover) rather than
 * accumulated into. */
export function withAppliedOptimization(
  current: TodayStats,
  today: string,
  event: AppliedOptimizationEvent,
): TodayStats {
  const base = current.date === today ? current : emptyStatsFor(today);
  return {
    date: today,
    promptsOptimized: base.promptsOptimized + 1,
    tokensSaved: base.tokensSaved + event.tokensSaved,
    reductionPercentageSum: base.reductionPercentageSum + event.reductionPercentage,
  };
}

/** `null` when there's nothing to average yet, rather than dividing by zero. */
export function averageReduction(stats: TodayStats): number | null {
  return stats.promptsOptimized > 0 ? stats.reductionPercentageSum / stats.promptsOptimized : null;
}
