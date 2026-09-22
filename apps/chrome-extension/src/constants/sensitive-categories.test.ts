import { describe, expect, it } from "vitest";
import { humanizeSensitiveCategories } from "./sensitive-categories.js";

describe("humanizeSensitiveCategories", () => {
  it("maps known categories to readable labels", () => {
    expect(humanizeSensitiveCategories(["email"])).toEqual(["an email address"]);
    expect(humanizeSensitiveCategories(["api_key"])).toEqual(["an API key"]);
  });

  it("de-duplicates and falls back for unknown categories", () => {
    const labels = humanizeSensitiveCategories(["email", "some_future_category"]);
    expect(labels).toHaveLength(2);
    expect(labels.join(" ")).not.toContain("some_future_category");
  });

  it("returns an empty array for no categories", () => {
    expect(humanizeSensitiveCategories([])).toEqual([]);
  });
});
