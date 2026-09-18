import { detectPlatform } from "../constants/platforms.js";
import { CLAUDE_SELECTORS } from "../constants/selectors.js";
import type { IPlatformAdapter } from "../types/platform-adapter.js";

export class ClaudeAdapter implements IPlatformAdapter {
  readonly id = "claude" as const;

  matches(url: string): boolean {
    return detectPlatform(url)?.id === this.id;
  }

  getInputElement(): HTMLElement | null {
    return document.querySelector<HTMLElement>(CLAUDE_SELECTORS.promptInput);
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

  onSubmitIntercept(callback: (text: string) => Promise<string>): void {
    const submitButton = document.querySelector<HTMLButtonElement>(CLAUDE_SELECTORS.submitButton);
    if (!submitButton) return;

    submitButton.addEventListener(
      "click",
      async (event) => {
        const current = this.getCurrentText();
        const finalText = await callback(current);
        if (finalText !== current) {
          event.preventDefault();
          event.stopImmediatePropagation();
          this.setText(finalText);
          submitButton.click();
        }
      },
      { capture: true },
    );
  }
}
