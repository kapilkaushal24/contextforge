import type { PrivacyPolicy } from "@ai-token-optimizer/contracts";
import { ModeSelector } from "../components/ModeSelector.js";
import { useSettings } from "../hooks/useSettings.js";

export function App(): JSX.Element {
  const { settings, update } = useSettings();

  if (!settings) {
    return <p className="p-6 text-sm text-gray-500">Loading settings…</p>;
  }

  return (
    <div className="mx-auto max-w-lg p-6 text-gray-900">
      <h1 className="text-lg font-semibold">AI Token Optimizer — Settings</h1>
      <p className="mt-1 text-sm text-gray-500">
        These defaults apply to every supported AI platform. Optimization is never applied
        without your explicit confirmation.
      </p>

      <div className="mt-6 flex flex-col gap-5">
        <ModeSelector
          value={settings.defaultMode}
          onChange={(defaultMode) => void update({ ...settings, defaultMode })}
        />

        <fieldset className="flex flex-col gap-2 text-sm">
          <legend className="font-medium text-gray-700">Privacy policy</legend>
          {(
            [
              { value: "cloud_allowed" as PrivacyPolicy, label: "Cloud allowed", desc: "May use cloud LLMs for semantic compression when deterministic optimization isn't enough." },
              { value: "local_only" as PrivacyPolicy, label: "Local only", desc: "Never sends prompt content to a cloud LLM provider." },
            ] satisfies { value: PrivacyPolicy; label: string; desc: string }[]
          ).map((option) => (
            <label key={option.value} className="flex items-start gap-2">
              <input
                type="radio"
                name="privacyPolicy"
                className="mt-1"
                checked={settings.privacyPolicy === option.value}
                onChange={() => void update({ ...settings, privacyPolicy: option.value })}
              />
              <span>
                <span className="block font-medium">{option.label}</span>
                <span className="block text-xs text-gray-500">{option.desc}</span>
              </span>
            </label>
          ))}
        </fieldset>
      </div>
    </div>
  );
}
