import { useEffect, useState } from "react";
import { PLATFORM_REGISTRY, detectPlatform, type PlatformDefinition } from "../constants/platforms.js";
import { ACTIVE_PLATFORM_KEY, getActivePlatform } from "../services/active-platform-store.js";

/**
 * The AI platform detected for the user's current tab. `undefined` while loading,
 * `null` when the active tab isn't a known platform (generic adapter applies).
 *
 * Resolves live via `chrome.tabs.query` (most accurate at the instant the popup
 * opens) and re-resolves whenever the background worker's tab-change listener
 * updates its cached state (see active-platform-store.ts / ADR-009) — so the popup
 * stays correct if the user switches tabs while it happens to be open.
 */
export function useActivePlatform(): PlatformDefinition | null | undefined {
  const [platform, setPlatform] = useState<PlatformDefinition | null | undefined>(undefined);

  useEffect(() => {
    let cancelled = false;

    async function resolve(): Promise<void> {
      const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
      if (cancelled) return;

      const liveMatch = detectPlatform(tab?.url);
      if (liveMatch) {
        setPlatform(liveMatch);
        return;
      }

      const stored = await getActivePlatform();
      if (cancelled) return;
      setPlatform(stored?.id ? (PLATFORM_REGISTRY.find((p) => p.id === stored.id) ?? null) : null);
    }

    void resolve();

    function onStorageChange(changes: Record<string, chrome.storage.StorageChange>, area: string): void {
      if (area === "session" && ACTIVE_PLATFORM_KEY in changes) void resolve();
    }

    chrome.storage.onChanged.addListener(onStorageChange);
    return () => {
      cancelled = true;
      chrome.storage.onChanged.removeListener(onStorageChange);
    };
  }, []);

  return platform;
}
