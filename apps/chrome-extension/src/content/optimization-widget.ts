import { requestOptimization } from "../services/messaging.js";
import { getSettings } from "../services/settings-store.js";
import type { IPlatformAdapter } from "../types/platform-adapter.js";
import {
  initialWidgetState,
  reduceWidgetState,
  type WidgetAction,
  type WidgetState,
} from "./optimization-widget-state.js";
import { OptimizationPanel } from "./panel.js";

const DEBOUNCE_MS = 400;
const ERROR_AUTO_DISMISS_MS = 6000;
/** How long after our own `setText` call to treat the resulting `input` event as
 * programmatic rather than the user typing (see optimization-widget-state.ts). */
const PROGRAMMATIC_WINDOW_MS = 300;

/**
 * Orchestrates the proactive optimization widget for one page: watches the adapter's
 * input element, drives the pure state machine (optimization-widget-state.ts), and
 * renders it via OptimizationPanel. The only two places this ever calls
 * `adapter.setText` are in direct response to the user clicking Apply or Undo.
 */
export class OptimizationWidget {
  private state: WidgetState = initialWidgetState;
  private readonly panel: OptimizationPanel;
  private debounceTimer: number | undefined;
  private errorDismissTimer: number | undefined;
  private programmaticUntil = 0;

  constructor(private readonly adapter: IPlatformAdapter) {
    this.panel = new OptimizationPanel(document.body, {
      onOptimize: () => void this.handleOptimize(),
      onApply: () => this.handleApply(),
      onReject: () => this.dispatch({ type: "REJECT_CLICKED" }),
      onUndo: () => this.handleUndo(),
      onDismiss: () => this.dispatch({ type: "DISMISS" }),
    });

    document.addEventListener("input", this.handleInput, true);
  }

  destroy(): void {
    document.removeEventListener("input", this.handleInput, true);
    window.clearTimeout(this.debounceTimer);
    window.clearTimeout(this.errorDismissTimer);
    this.panel.destroy();
  }

  private readonly handleInput = (event: Event): void => {
    const input = this.adapter.getInputElement();
    if (!input || event.target !== input) return;

    const origin = Date.now() <= this.programmaticUntil ? "programmatic" : "user";
    window.clearTimeout(this.debounceTimer);
    this.debounceTimer = window.setTimeout(() => {
      this.dispatch({ type: "TEXT_CHANGED", text: this.adapter.getCurrentText(), origin });
    }, DEBOUNCE_MS);
  };

  private dispatch(action: WidgetAction): void {
    const next = reduceWidgetState(this.state, action);
    if (next === this.state) return;
    this.state = next;

    window.clearTimeout(this.errorDismissTimer);
    if (next.phase === "error") {
      this.errorDismissTimer = window.setTimeout(() => this.dispatch({ type: "DISMISS" }), ERROR_AUTO_DISMISS_MS);
    }

    this.panel.render(next);
  }

  /** Indirection that defeats TS's (here incorrect) narrowing of `this.state` across
   * `await` boundaries — see the call site in handleOptimize for why this exists. */
  private getState(): WidgetState {
    return this.state;
  }

  private async handleOptimize(): Promise<void> {
    if (this.state.phase !== "idle") return;
    const { text } = this.state;
    this.dispatch({ type: "OPTIMIZE_CLICKED" });

    const settings = await getSettings();
    const response = await requestOptimization(text, this.adapter.id, settings.defaultMode, settings.privacyPolicy);

    // The user may have kept typing (or dismissed) while the request was in flight;
    // only act on the response if we're still waiting on this exact request. Read via
    // `getState()` rather than `this.state` directly — TS's control-flow narrowing
    // incorrectly carries the "idle" narrowing from above across the `await`, since it
    // can't see that `dispatch()` mutates `this.state` in between.
    if (this.getState().phase !== "loading") return;
    if (response.ok) {
      this.dispatch({ type: "OPTIMIZE_SUCCEEDED", result: response.result });
    } else {
      this.dispatch({ type: "OPTIMIZE_FAILED", message: response.error });
    }
  }

  private handleApply(): void {
    if (this.state.phase !== "result") return;
    const { optimizedText } = this.state.result;
    this.dispatch({ type: "APPLY_CLICKED" });
    this.setTextProgrammatically(optimizedText);
  }

  private handleUndo(): void {
    if (this.state.phase !== "applied") return;
    const { previousText } = this.state;
    this.dispatch({ type: "UNDO_CLICKED" });
    this.setTextProgrammatically(previousText);
  }

  private setTextProgrammatically(text: string): void {
    this.programmaticUntil = Date.now() + PROGRAMMATIC_WINDOW_MS;
    this.adapter.setText(text);
  }
}
