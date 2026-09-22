import type { Platform } from "@ai-token-optimizer/contracts";

/**
 * Encapsulates all DOM-specific knowledge for one AI platform. Selectors live only
 * inside a concrete adapter (see src/constants/selectors.ts + src/adapters/*) — the
 * rest of the extension only ever talks to this interface, so a site's DOM changing
 * requires editing exactly one adapter file.
 *
 * Deliberately has no submit-interception hook (an earlier scaffold had one that
 * silently swapped the input's text and re-clicked Send). That violates the "never
 * silently modify a user's prompt without an explicit Apply" contract
 * (docs/architecture/chrome-extension.md §6) and is fragile against
 * React-controlled inputs. Instead, the content script (see
 * content/optimization-widget.ts) shows a proactive indicator while the user types
 * and only ever calls `setText` in direct response to the user clicking Apply.
 */
export interface IPlatformAdapter {
  readonly id: Platform;

  /** Whether this adapter should activate for the given page URL. */
  matches(url: string): boolean;

  /** Locates the prompt input element on the page, if present. */
  getInputElement(): HTMLElement | null;

  /** Reads the user's current, not-yet-submitted prompt text. */
  getCurrentText(): string;

  /** Replaces the prompt input's text (used when the user clicks Apply). */
  setText(text: string): void;

  /** Optional: prior turns, used only by context-mode optimization. */
  extractConversationContext?(): string[];
}
