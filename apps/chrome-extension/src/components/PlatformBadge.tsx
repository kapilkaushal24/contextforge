import type { PlatformDefinition } from "../constants/platforms.js";

interface PlatformBadgeProps {
  platform: PlatformDefinition | null | undefined;
}

/** Shows which AI platform was auto-detected on the user's active tab (ADR-009). */
export function PlatformBadge({ platform }: PlatformBadgeProps): JSX.Element {
  if (platform === undefined) {
    return <span className="text-xs text-gray-400">Detecting current tab…</span>;
  }

  if (platform === null) {
    return (
      <span className="inline-flex items-center gap-1.5 rounded-full bg-gray-100 px-2 py-0.5 text-xs text-gray-500">
        <span className="h-1.5 w-1.5 rounded-full bg-gray-400" />
        Not on a supported AI site
      </span>
    );
  }

  return (
    <span className="inline-flex items-center gap-1.5 rounded-full bg-green-50 px-2 py-0.5 text-xs text-green-700">
      <span className="h-1.5 w-1.5 rounded-full bg-green-500" />
      Detected: {platform.displayName}
    </span>
  );
}
