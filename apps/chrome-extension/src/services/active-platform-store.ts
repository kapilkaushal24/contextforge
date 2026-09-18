import { detectPlatform } from "../constants/platforms.js";

/**
 * Tracks which known AI platform the user's active tab currently belongs to.
 * Written by the background service worker's tab listeners (see
 * background/service-worker.ts) whenever the user switches tabs or a tab finishes
 * navigating; read by the popup (useActivePlatform) and available to any future
 * consumer (e.g. a content-script badge) without each one re-deriving it.
 *
 * `chrome.storage.session` is in-memory and cleared on browser restart — appropriate
 * here since this is derived, ephemeral state, never anything worth persisting.
 */
export const ACTIVE_PLATFORM_KEY = "aito.activePlatform" as const;

export interface ActivePlatformState {
  id: string | null;
  displayName: string | null;
  tabId: number | null;
}

export async function setActivePlatform(tab: chrome.tabs.Tab): Promise<ActivePlatformState> {
  const platform = detectPlatform(tab.url);
  const state: ActivePlatformState = {
    id: platform?.id ?? null,
    displayName: platform?.displayName ?? null,
    tabId: tab.id ?? null,
  };
  await chrome.storage.session.set({ [ACTIVE_PLATFORM_KEY]: state });
  return state;
}

export async function getActivePlatform(): Promise<ActivePlatformState | null> {
  const stored = await chrome.storage.session.get(ACTIVE_PLATFORM_KEY);
  return (stored[ACTIVE_PLATFORM_KEY] as ActivePlatformState | undefined) ?? null;
}
