import type { OptimizeResult } from "@ai-token-optimizer/contracts";
import { describe, expect, it } from "vitest";
import {
  MIN_WORDS_TO_SHOW,
  reduceWidgetState,
  wordCount,
  type WidgetState,
} from "./optimization-widget-state.js";

const SHORT_TEXT = "fix this";
const LONG_TEXT = "please review this function for bugs and performance issues thoroughly";

const RESULT: OptimizeResult = {
  originalText: LONG_TEXT,
  optimizedText: "review this function for bugs and performance",
  originalTokens: 20,
  optimizedTokens: 12,
  tokensSaved: 8,
  reductionPercentage: 40,
  estimatedCostSaved: 0.001,
  optimizationMode: "balanced",
  confidence: 0.95,
  semanticSimilarity: 0.95,
  constraintPreservation: 1,
  requiresReview: false,
  reviewReasons: [],
  changes: [],
};

function typed(state: WidgetState, text: string): WidgetState {
  return reduceWidgetState(state, { type: "TEXT_CHANGED", text, origin: "user" });
}

describe("wordCount", () => {
  it("counts words, ignoring surrounding whitespace", () => {
    expect(wordCount("   ")).toBe(0);
    expect(wordCount("")).toBe(0);
    expect(wordCount("one two   three")).toBe(3);
  });

  it("MIN_WORDS_TO_SHOW is the exact boundary used by the reducer", () => {
    const atBoundary = Array.from({ length: MIN_WORDS_TO_SHOW }, () => "x").join(" ");
    const belowBoundary = Array.from({ length: MIN_WORDS_TO_SHOW - 1 }, () => "x").join(" ");
    expect(typed({ phase: "hidden" }, atBoundary).phase).toBe("idle");
    expect(typed({ phase: "hidden" }, belowBoundary).phase).toBe("hidden");
  });
});

describe("TEXT_CHANGED (user)", () => {
  it("stays hidden for short text", () => {
    expect(typed({ phase: "hidden" }, SHORT_TEXT)).toEqual({ phase: "hidden" });
  });

  it("becomes idle once there is enough text", () => {
    expect(typed({ phase: "hidden" }, LONG_TEXT)).toEqual({ phase: "idle", text: LONG_TEXT });
  });

  it("resets an in-progress result back to idle/hidden when the user edits", () => {
    const resultState: WidgetState = { phase: "result", text: LONG_TEXT, result: RESULT };
    expect(typed(resultState, "edited " + LONG_TEXT).phase).toBe("idle");
    expect(typed(resultState, "hi").phase).toBe("hidden");
  });

  it("resets an applied state back to idle when the user types further", () => {
    const appliedState: WidgetState = { phase: "applied", result: RESULT, previousText: LONG_TEXT };
    const next = typed(appliedState, "now the user adds even more words to this prompt");
    expect(next.phase).toBe("idle");
  });
});

describe("TEXT_CHANGED (programmatic)", () => {
  it("never changes phase — Apply/Undo's own setText must not reset the widget", () => {
    const loading: WidgetState = { phase: "loading", text: LONG_TEXT };
    const next = reduceWidgetState(loading, {
      type: "TEXT_CHANGED",
      text: "anything",
      origin: "programmatic",
    });
    expect(next).toBe(loading);
  });
});

describe("optimize flow", () => {
  it("idle -> loading -> result on success", () => {
    const idle: WidgetState = { phase: "idle", text: LONG_TEXT };
    const loading = reduceWidgetState(idle, { type: "OPTIMIZE_CLICKED" });
    expect(loading).toEqual({ phase: "loading", text: LONG_TEXT });

    const result = reduceWidgetState(loading, { type: "OPTIMIZE_SUCCEEDED", result: RESULT });
    expect(result).toEqual({ phase: "result", text: LONG_TEXT, result: RESULT });
  });

  it("idle -> loading -> error on failure, and DISMISS returns to idle", () => {
    const loading: WidgetState = { phase: "loading", text: LONG_TEXT };
    const error = reduceWidgetState(loading, { type: "OPTIMIZE_FAILED", message: "network error" });
    expect(error).toEqual({ phase: "error", text: LONG_TEXT, message: "network error" });

    const dismissed = reduceWidgetState(error, { type: "DISMISS" });
    expect(dismissed).toEqual({ phase: "idle", text: LONG_TEXT });
  });

  it("OPTIMIZE_CLICKED is a no-op outside idle", () => {
    const hidden: WidgetState = { phase: "hidden" };
    expect(reduceWidgetState(hidden, { type: "OPTIMIZE_CLICKED" })).toBe(hidden);
  });
});

describe("apply / reject / undo", () => {
  const resultState: WidgetState = { phase: "result", text: LONG_TEXT, result: RESULT };

  it("APPLY_CLICKED moves to applied, remembering the pre-optimization text for undo", () => {
    const applied = reduceWidgetState(resultState, { type: "APPLY_CLICKED" });
    expect(applied).toEqual({ phase: "applied", result: RESULT, previousText: LONG_TEXT });
  });

  it("REJECT_CLICKED discards the result and returns to idle with the original text", () => {
    const rejected = reduceWidgetState(resultState, { type: "REJECT_CLICKED" });
    expect(rejected).toEqual({ phase: "idle", text: LONG_TEXT });
  });

  it("UNDO_CLICKED returns to idle with the pre-optimization text restored", () => {
    const appliedState: WidgetState = { phase: "applied", result: RESULT, previousText: LONG_TEXT };
    const undone = reduceWidgetState(appliedState, { type: "UNDO_CLICKED" });
    expect(undone).toEqual({ phase: "idle", text: LONG_TEXT });
  });

  it("APPLY/REJECT/UNDO are no-ops in the wrong phase", () => {
    const idle: WidgetState = { phase: "idle", text: LONG_TEXT };
    expect(reduceWidgetState(idle, { type: "APPLY_CLICKED" })).toBe(idle);
    expect(reduceWidgetState(idle, { type: "REJECT_CLICKED" })).toBe(idle);
    expect(reduceWidgetState(idle, { type: "UNDO_CLICKED" })).toBe(idle);
  });
});
