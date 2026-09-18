import { ModeSelector } from "../components/ModeSelector.js";
import { PlatformBadge } from "../components/PlatformBadge.js";
import { useActivePlatform } from "../hooks/useActivePlatform.js";
import { useSettings } from "../hooks/useSettings.js";

export function App(): JSX.Element {
  const { settings, update } = useSettings();
  const activePlatform = useActivePlatform();

  return (
    <div className="w-80 p-4 text-gray-900">
      <header className="mb-3">
        <h1 className="text-base font-semibold">AI Token Optimizer</h1>
        <p className="text-xs text-gray-500">Reduce token usage without losing your intent.</p>
        <div className="mt-2">
          <PlatformBadge platform={activePlatform} />
        </div>
      </header>

      {settings ? (
        <ModeSelector
          value={settings.defaultMode}
          onChange={(defaultMode) => void update({ ...settings, defaultMode })}
        />
      ) : (
        <p className="text-xs text-gray-500">Loading settings…</p>
      )}

      <section className="mt-4 rounded-md bg-gray-50 p-3 text-sm">
        <h2 className="mb-1 font-medium">Today</h2>
        <dl className="grid grid-cols-2 gap-y-1 text-xs text-gray-600">
          <dt>Prompts optimized</dt>
          <dd className="text-right font-mono">—</dd>
          <dt>Tokens saved</dt>
          <dd className="text-right font-mono">—</dd>
          <dt>Avg. reduction</dt>
          <dd className="text-right font-mono">—</dd>
        </dl>
        <p className="mt-2 text-[11px] text-gray-400">
          Stats populate once the optimization backend is connected (Phase 5+).
        </p>
      </section>

      <footer className="mt-3 flex justify-end">
        <a
          className="text-xs text-blue-600 hover:underline"
          href="../options/index.html"
          target="_blank"
          rel="noreferrer"
        >
          Settings
        </a>
      </footer>
    </div>
  );
}
