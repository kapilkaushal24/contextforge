import { describe, expect, it } from "vitest";
import { averageReduction, emptyStatsFor, todayDateKey, withAppliedOptimization } from "./stats.js";

describe("todayDateKey", () => {
  it("formats as zero-padded local YYYY-MM-DD", () => {
    expect(todayDateKey(new Date(2026, 0, 5))).toBe("2026-01-05");
    expect(todayDateKey(new Date(2026, 10, 23))).toBe("2026-11-23");
  });
});

describe("withAppliedOptimization", () => {
  it("accumulates counters for the same day", () => {
    const day1 = withAppliedOptimization(emptyStatsFor("2026-01-05"), "2026-01-05", {
      tokensSaved: 10,
      reductionPercentage: 20,
    });
    const day1b = withAppliedOptimization(day1, "2026-01-05", { tokensSaved: 5, reductionPercentage: 40 });

    expect(day1b).toEqual({
      date: "2026-01-05",
      promptsOptimized: 2,
      tokensSaved: 15,
      reductionPercentageSum: 60,
    });
  });

  it("resets instead of accumulating when the stored stats are from an earlier day", () => {
    const yesterday = withAppliedOptimization(emptyStatsFor("2026-01-04"), "2026-01-04", {
      tokensSaved: 100,
      reductionPercentage: 50,
    });

    const today = withAppliedOptimization(yesterday, "2026-01-05", { tokensSaved: 8, reductionPercentage: 30 });

    expect(today).toEqual({
      date: "2026-01-05",
      promptsOptimized: 1,
      tokensSaved: 8,
      reductionPercentageSum: 30,
    });
  });
});

describe("averageReduction", () => {
  it("returns null when nothing has been optimized yet", () => {
    expect(averageReduction(emptyStatsFor("2026-01-05"))).toBeNull();
  });

  it("averages the reduction percentage across applied optimizations", () => {
    const stats = withAppliedOptimization(
      withAppliedOptimization(emptyStatsFor("2026-01-05"), "2026-01-05", {
        tokensSaved: 10,
        reductionPercentage: 20,
      }),
      "2026-01-05",
      { tokensSaved: 10, reductionPercentage: 40 },
    );

    expect(averageReduction(stats)).toBe(30);
  });
});
