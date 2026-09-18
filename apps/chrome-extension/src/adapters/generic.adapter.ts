import type { IPlatformAdapter } from "../types/platform-adapter.js";

/**
 * Fallback adapter for any page not covered by a dedicated adapter. It uses a
 * best-effort heuristic (largest visible `<textarea>` or `contenteditable`) so the
 * extension degrades gracefully instead of doing nothing on unsupported sites.
 */
export class GenericAdapter implements IPlatformAdapter {
  readonly id = "generic" as const;

  matches(_url: string): boolean {
    // Always eligible as the last-resort fallback; the factory only selects it
    // when no platform-specific adapter matched.
    return true;
  }

  getInputElement(): HTMLElement | null {
    const candidates = Array.from(
      document.querySelectorAll<HTMLElement>('textarea, [contenteditable="true"]'),
    );
    if (candidates.length === 0) return null;

    return candidates.reduce((largest, el) => {
      const area = el.getBoundingClientRect().width * el.getBoundingClientRect().height;
      const largestArea = largest.getBoundingClientRect().width * largest.getBoundingClientRect().height;
      return area > largestArea ? el : largest;
    });
  }

  getCurrentText(): string {
    const el = this.getInputElement();
    if (!el) return "";
    return el instanceof HTMLTextAreaElement ? el.value : (el.textContent ?? "");
  }

  setText(text: string): void {
    const el = this.getInputElement();
    if (!el) return;
    if (el instanceof HTMLTextAreaElement) {
      el.value = text;
      el.dispatchEvent(new Event("input", { bubbles: true }));
    } else {
      el.textContent = text;
      el.dispatchEvent(new InputEvent("input", { bubbles: true }));
    }
  }

  onSubmitIntercept(_callback: (text: string) => Promise<string>): void {
    // The generic adapter has no reliable submit-button selector; interception is
    // opt-in per site and left unimplemented here rather than guessed at.
  }
}
