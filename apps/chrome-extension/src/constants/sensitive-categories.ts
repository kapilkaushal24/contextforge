/** Maps `OptimizeResult.sensitiveContentCategories` codes to short, user-facing
 * labels — same rationale as constants/review-reasons.ts: never show the raw API
 * category code, and never the matched text itself (the API never sends it either). */
const CATEGORY_LABELS: Record<string, string> = {
  email: "an email address",
  phone: "a phone number",
  ssn: "a social security number",
  credit_card: "a credit card number",
  api_key: "an API key",
};

const FALLBACK_LABEL = "sensitive content";

export function humanizeSensitiveCategories(categories: readonly string[]): string[] {
  return Array.from(new Set(categories.map((c) => CATEGORY_LABELS[c] ?? FALLBACK_LABEL)));
}
