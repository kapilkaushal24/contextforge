import type { TokenizerProvider } from "./enums.js";

/** POST /api/v1/estimate-tokens request body. */
export interface EstimateTokensRequest {
  text: string;
  provider: TokenizerProvider;
}

export interface EstimateTokensResponse {
  tokens: number;
  provider: TokenizerProvider;
  /** Distinguishes our estimate from a real provider-reported count (never conflate the two). */
  method: "estimated" | "provider_reported";
}
