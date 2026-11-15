import { useEffect, useState } from "react";
import { getTodayStats, TODAY_STATS_KEY } from "../services/stats-store.js";
import type { TodayStats } from "../services/stats.js";

/** `undefined` while loading. Re-resolves whenever another part of the extension
 * (the content-script widget's Apply handler) records a new stat while the popup is
 * open, via chrome.storage.onChanged — same live-update pattern as useActivePlatform. */
export function useTodayStats(): TodayStats | undefined {
  const [stats, setStats] = useState<TodayStats | undefined>(undefined);

  useEffect(() => {
    let cancelled = false;

    function refresh(): void {
      void getTodayStats().then((next) => {
        if (!cancelled) setStats(next);
      });
    }

    refresh();

    function onStorageChange(changes: Record<string, chrome.storage.StorageChange>, area: string): void {
      if (area === "local" && TODAY_STATS_KEY in changes) refresh();
    }

    chrome.storage.onChanged.addListener(onStorageChange);
    return () => {
      cancelled = true;
      chrome.storage.onChanged.removeListener(onStorageChange);
    };
  }, []);

  return stats;
}
