/**
 * Shared enums for the optimization API. Kept as string unions (not TS `enum`) so
 * values serialize identically to the Python side's `str, Enum` classes and to JSON.
 */

export type OptimizationMode =
  | "conservative"
  | "balanced"
  | "aggressive"
  | "code"
  | "context";

export type PrivacyPolicy = "cloud_allowed" | "local_only";

/**
 * Platform id, as used by `IPlatformAdapter.id` and reported to the API.
 *
 * Deliberately an open `string`, not a closed union — the set of known platforms is
 * defined by the extension's platform registry (apps/chrome-extension/src/constants/
 * platforms.ts) and auto-detected from the active tab's URL, not hardcoded here or
 * anywhere else (ADR-009). "generic" is reserved for any unrecognized platform.
 */
export type Platform = string;

export type PromptType = "code" | "documentation" | "conversation" | "general";

export type TokenizerProvider = "openai" | "anthropic" | "gemini" | "generic";

export type ChangeImpact = "low" | "medium" | "high";

export type ChangeType =
  | "deduplication"
  | "whitespace_cleanup"
  | "boilerplate_removal"
  | "structural_rewrite"
  | "semantic_compression"
  | "context_deduplication";

export type FeedbackRating = "helpful" | "not_helpful";

export type FeedbackReason = "changed_intent" | "too_aggressive" | "other";
