import { describe, expect, it } from "vitest";
import { estimateTokensLocally } from "./local-token-estimate.js";

describe("estimateTokensLocally", () => {
  it("is zero for empty/whitespace text", () => {
    expect(estimateTokensLocally("")).toBe(0);
    expect(estimateTokensLocally("   \n  ")).toBe(0);
  });

  it("is at least 1 for any non-empty text", () => {
    expect(estimateTokensLocally("a")).toBe(1);
  });

  it("grows roughly with length", () => {
    const short = estimateTokensLocally("a".repeat(20));
    const long = estimateTokensLocally("a".repeat(200));
    expect(long).toBeGreaterThan(short);
  });
});
