/**
 * Single source of truth for which AI platforms this extension recognizes and how to
 * recognize a tab as belonging to one. Adding a platform means adding one entry here —
 * no other file should hardcode a platform id as a literal string/enum member.
 *
 * Consumed by:
 *  - manifest.config.ts        (derives content_scripts.matches / host_permissions)
 *  - adapters/*.adapter.ts     (matches() delegates to detectPlatform)
 *  - background/service-worker (tab-switch auto-detection, see below)
 *  - hooks/useActivePlatform   (popup live detection)
 */
export interface PlatformDefinition {
  readonly id: string;
  readonly displayName: string;
  readonly urlPatterns: readonly RegExp[];
  /** Origin patterns in Chrome match-pattern syntax; must cover the same URLs as urlPatterns. */
  readonly originPatterns: readonly string[];
}

export const PLATFORM_REGISTRY: readonly PlatformDefinition[] = [
  {
    id: "chatgpt",
    displayName: "ChatGPT",
    urlPatterns: [/^https:\/\/chat\.openai\.com\//, /^https:\/\/chatgpt\.com\//],
    originPatterns: ["https://chat.openai.com/*", "https://chatgpt.com/*"],
  },
  {
    id: "claude",
    displayName: "Claude",
    urlPatterns: [/^https:\/\/claude\.ai\//],
    originPatterns: ["https://claude.ai/*"],
  },
];

/** Resolves a tab/page URL to a known platform; undefined means the generic adapter applies. */
export function detectPlatform(url: string | undefined | null): PlatformDefinition | undefined {
  if (!url) return undefined;
  return PLATFORM_REGISTRY.find((platform) => platform.urlPatterns.some((pattern) => pattern.test(url)));
}

/** Flattened origin patterns for every registered platform — feeds the manifest. */
export function allOriginPatterns(): string[] {
  return PLATFORM_REGISTRY.flatMap((platform) => platform.originPatterns);
}
