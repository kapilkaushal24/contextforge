import type { OptimizationMode } from "@ai-token-optimizer/contracts";

const MODES: { value: OptimizationMode; label: string }[] = [
  { value: "conservative", label: "Conservative" },
  { value: "balanced", label: "Balanced" },
  { value: "aggressive", label: "Aggressive" },
  { value: "code", label: "Code" },
  { value: "context", label: "Context" },
];

interface ModeSelectorProps {
  value: OptimizationMode;
  onChange: (mode: OptimizationMode) => void;
}

export function ModeSelector({ value, onChange }: ModeSelectorProps): JSX.Element {
  return (
    <label className="flex flex-col gap-1 text-sm">
      <span className="font-medium text-gray-700">Optimization mode</span>
      <select
        className="rounded-md border border-gray-300 px-2 py-1.5 text-sm focus:border-blue-500 focus:outline-none"
        value={value}
        onChange={(event) => onChange(event.target.value as OptimizationMode)}
      >
        {MODES.map((mode) => (
          <option key={mode.value} value={mode.value}>
            {mode.label}
          </option>
        ))}
      </select>
    </label>
  );
}
