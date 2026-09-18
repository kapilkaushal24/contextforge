import type { OptimizationMode, PrivacyPolicy } from "./enums.js";

/** GET /api/v1/usage response — aggregated only, never raw prompt text. */
export interface UsageSummary {
  rangeStart: string; // ISO date
  rangeEnd: string; // ISO date
  totalRequests: number;
  totalTokensSaved: number;
  averageReductionPercentage: number;
  estimatedCostSaved: number;
}

/** GET/PUT /api/v1/settings body. */
export interface UserSettings {
  defaultMode: OptimizationMode;
  privacyPolicy: PrivacyPolicy;
  featureFlags: Record<string, boolean>;
}

/** POST /api/v1/feedback request body. */
export interface FeedbackRequest {
  requestId: string;
  rating: "helpful" | "not_helpful";
  reason?: "changed_intent" | "too_aggressive" | "other";
}
