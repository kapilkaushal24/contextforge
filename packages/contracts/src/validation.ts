/** POST /api/v1/validate request body. */
export interface ValidateRequest {
  originalText: string;
  optimizedText: string;
}

/**
 * Semantic validation result. All scores are 0..1. When `confidence` is below the
 * configured threshold, the pipeline marks the result `requiresReview` and the caller
 * must not auto-apply the optimization (see ADR on semantic validation gate).
 */
export interface SemanticValidationResult {
  semanticSimilarity: number;
  constraintPreservation: number;
  confidence: number;
  /** Same stable reason codes as `OptimizeResult.reviewReasons`. */
  issues: string[];
}
