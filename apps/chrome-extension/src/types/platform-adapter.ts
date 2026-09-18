import type { Platform } from "@ai-token-optimizer/contracts";

/**
 * Encapsulates all DOM-specific knowledge for one AI platform. Selectors live only
 * inside a concrete adapter (see src/constants/selectors.ts + src/adapters/*) — the
 * rest of the extension only ever talks to this interface, so a site's DOM changing
 * requires editing exactly one adapter file.
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

  /**
   * Registers a callback invoked just before the user's prompt would be submitted.
   * The callback receives the current text and returns the text that should actually
   * be submitted (unchanged unless the user has applied an optimization).
   */
  onSubmitIntercept(callback: (text: string) => Promise<string>): void;

  /** Optional: prior turns, used only by context-mode optimization. */
  extractConversationContext?(): string[];
}
