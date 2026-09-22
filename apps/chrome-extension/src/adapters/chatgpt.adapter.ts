import { detectPlatform } from "../constants/platforms.js";
import { CHATGPT_SELECTORS } from "../constants/selectors.js";
import type { IPlatformAdapter } from "../types/platform-adapter.js";

/**
 * Selectors: `promptInput` — the composer's contenteditable div (`#prompt-textarea`).
 * `submitButton` is defined in constants/selectors.ts for documentation but
 * deliberately unused here — see the no-submit-interception note in
 * types/platform-adapter.ts.
 */

export class ChatGptAdapter implements IPlatformAdapter {
  readonly id = "chatgpt" as const;

  matches(url: string): boolean {
    return detectPlatform(url)?.id === this.id;
  }

  getInputElement(): HTMLElement | null {
    return document.querySelector<HTMLElement>(CHATGPT_SELECTORS.promptInput);
  }

  getCurrentText(): string {
    return this.getInputElement()?.textContent ?? "";
  }

  setText(text: string): void {
    const el = this.getInputElement();
    if (!el) return;
    el.textContent = text;
    el.dispatchEvent(new InputEvent("input", { bubbles: true }));
  }
}
