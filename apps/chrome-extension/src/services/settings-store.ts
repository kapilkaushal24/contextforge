import type { OptimizationMode, PrivacyPolicy } from "@ai-token-optimizer/contracts";

export interface StoredSettings {
  defaultMode: OptimizationMode;
  privacyPolicy: PrivacyPolicy;
}

const SETTINGS_KEY = "aito.settings" as const;

const DEFAULT_SETTINGS: StoredSettings = {
  defaultMode: "balanced",
  privacyPolicy: "cloud_allowed",
};

/** Thin wrapper over `chrome.storage.sync` — the one place settings persistence lives. */
export async function getSettings(): Promise<StoredSettings> {
  const stored = await chrome.storage.sync.get(SETTINGS_KEY);
  return { ...DEFAULT_SETTINGS, ...(stored[SETTINGS_KEY] as Partial<StoredSettings> | undefined) };
}

export async function setSettings(settings: StoredSettings): Promise<void> {
  await chrome.storage.sync.set({ [SETTINGS_KEY]: settings });
}
