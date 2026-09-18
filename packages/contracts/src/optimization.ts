import type { ChangeImpact, ChangeType, OptimizationMode, Platform, PrivacyPolicy } from "./enums.js";

/** POST /api/v1/optimize request body. */
export interface OptimizeRequest {
  /** Required, non-empty, max 100_000 chars (enforced server-side). */
  text: string;
  platform: Platform;
  mode: OptimizationMode;
  privacyPolicy: PrivacyPolicy;
  /** Prior turns, only used by context-mode optimization. */
  conversationContext?: string[];
}

export interface OptimizationChange {
  type: ChangeType;
  description: string;
  impact: ChangeImpact;
}

/** POST /api/v1/optimize response body. */
export interface OptimizeResult {
  originalText: string;
  optimizedText: string;
  originalTokens: number;
  optimizedTokens: number;
  tokensSaved: number;
  reductionPercentage: number;
  /** Estimate only — never provider-billed actuals. Label accordingly in the UI. */
  estimatedCostSaved: number;
  optimizationMode: OptimizationMode;
  /** 0..1 semantic validation confidence. */
  confidence: number;
  /** True when confidence is below threshold — UI must not auto-apply. */
  requiresReview: boolean;
  changes: OptimizationChange[];
}
