import type { OptimizeResult } from "@ai-token-optimizer/contracts";

/**
 * Pure state machine for the in-page optimization widget (content/optimization-widget.ts
 * wires this to the DOM). Kept framework-free and side-effect-free so every transition is
 * unit-testable without a browser — see optimization-widget-state.test.ts.
 *
 * Invariant this machine exists to enforce: `setText` is only ever reached via APPLY_CLICKED
 * or UNDO_CLICKED, both of which require an explicit user click. No other path — including a
 * failed optimize call — may result in the prompt being modified (docs/architecture/
 * chrome-extension.md §6, "never silently modify a user's prompt without an explicit Apply").
 */

/** Minimum words before the widget shows anything — avoids noise on short prompts. */
export const MIN_WORDS_TO_SHOW = 8;

export type WidgetState =
  | { phase: "hidden" }
  | { phase: "idle"; text: string }
  | { phase: "loading"; text: string }
  | { phase: "result"; text: string; result: OptimizeResult }
  | { phase: "applied"; result: OptimizeResult; previousText: string }
  | { phase: "error"; text: string; message: string };

export type WidgetAction =
  | { type: "TEXT_CHANGED"; text: string; origin: "user" | "programmatic" }
  | { type: "OPTIMIZE_CLICKED" }
  | { type: "OPTIMIZE_SUCCEEDED"; result: OptimizeResult }
  | { type: "OPTIMIZE_FAILED"; message: string }
  | { type: "APPLY_CLICKED" }
  | { type: "REJECT_CLICKED" }
  | { type: "UNDO_CLICKED" }
  | { type: "DISMISS" };

export function wordCount(text: string): number {
  const trimmed = text.trim();
  return trimmed === "" ? 0 : trimmed.split(/\s+/).length;
}

function idleOrHidden(text: string): WidgetState {
  return wordCount(text) >= MIN_WORDS_TO_SHOW ? { phase: "idle", text } : { phase: "hidden" };
}

export const initialWidgetState: WidgetState = { phase: "hidden" };

export function reduceWidgetState(state: WidgetState, action: WidgetAction): WidgetState {
  switch (action.type) {
    case "TEXT_CHANGED": {
      // A programmatic change (our own Apply/Undo call) must not reset the phase that
      // triggered it — only a change the user typed does.
      if (action.origin === "programmatic") {
        return state;
      }
      return idleOrHidden(action.text);
    }

    case "OPTIMIZE_CLICKED":
      return state.phase === "idle" ? { phase: "loading", text: state.text } : state;

    case "OPTIMIZE_SUCCEEDED":
      return state.phase === "loading"
        ? { phase: "result", text: state.text, result: action.result }
        : state;

    case "OPTIMIZE_FAILED":
      return state.phase === "loading"
        ? { phase: "error", text: state.text, message: action.message }
        : state;

    case "APPLY_CLICKED":
      return state.phase === "result"
        ? { phase: "applied", result: state.result, previousText: state.text }
        : state;

    case "REJECT_CLICKED":
      return state.phase === "result" ? idleOrHidden(state.text) : state;

    case "UNDO_CLICKED":
      return state.phase === "applied" ? idleOrHidden(state.previousText) : state;

    case "DISMISS":
      return state.phase === "error" ? idleOrHidden(state.text) : state;

    default: {
      const exhaustive: never = action;
      return exhaustive;
    }
  }
}
