import { describe, expect, it } from "vitest";
import { humanizeReviewReason, humanizeReviewReasons } from "./review-reasons.js";

describe("humanizeReviewReason", () => {
  it("maps known codes to readable text", () => {
    expect(humanizeReviewReason("missing_negations")).toMatch(/not\/never\/only/);
    expect(humanizeReviewReason("missing_numbers")).toMatch(/number/);
  });

  it("falls back for an unknown code instead of leaking it to the UI", () => {
    const label = humanizeReviewReason("some_future_code_v2");
    expect(label).not.toContain("some_future_code_v2");
    expect(label.length).toBeGreaterThan(0);
  });
});

describe("humanizeReviewReasons", () => {
  it("de-duplicates reasons that map to the same label", () => {
    const labels = humanizeReviewReasons(["missing_identifiers", "missing_quoted_literals", "nope", "nope2"]);
    expect(labels).toHaveLength(2);
  });

  it("returns an empty array for no reasons", () => {
    expect(humanizeReviewReasons([])).toEqual([]);
  });
});
