import { useEffect, useState } from "react";
import { getSettings, setSettings, type StoredSettings } from "../services/settings-store.js";

export function useSettings(): {
  settings: StoredSettings | null;
  update: (next: StoredSettings) => Promise<void>;
} {
  const [settings, setLocalSettings] = useState<StoredSettings | null>(null);

  useEffect(() => {
    void getSettings().then(setLocalSettings);
  }, []);

  async function update(next: StoredSettings): Promise<void> {
    await setSettings(next);
    setLocalSettings(next);
  }

  return { settings, update };
}
