/**
 * Maps the API's stable `reviewReasons`/`issues` codes to short, user-facing text.
 * The API contract explicitly says these codes are not meant for display — this is
 * the one place that translation happens (packages/contracts/src/optimization.ts).
 */
const REASON_LABELS: Record<string, string> = {
  missing_fenced_code: "a code block may have changed",
  missing_numbers: "a number may have been dropped",
  missing_identifiers: "a name or identifier may have been dropped",
  missing_quoted_literals: "a quoted phrase may have been dropped",
  missing_negations: "a “not/never/only” constraint may have been dropped",
  missing_constraint_words: "a requirement may have been softened",
  missing_format_terms: "an output-format requirement may have changed",
  missing_entities: "a named detail may have been dropped",
  introduced_content: "new content may have been added",
  empty_output: "the optimized text came back empty",
  not_shorter: "the rewrite was not actually shorter",
};

const FALLBACK_LABEL = "the meaning may have changed";

export function humanizeReviewReason(code: string): string {
  return REASON_LABELS[code] ?? FALLBACK_LABEL;
}

/** De-duplicated, human-readable reasons, always at least one entry if codes is non-empty. */
export function humanizeReviewReasons(codes: readonly string[]): string[] {
  return Array.from(new Set(codes.map(humanizeReviewReason)));
}
