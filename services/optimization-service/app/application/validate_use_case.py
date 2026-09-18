"""Placeholder semantic validation (Phase 5 skeleton): full confidence for identical
text, otherwise a naive word-overlap ratio. Replaced by the real `ISemanticValidator`
in Phase 9 (docs/architecture/ai-ml.md §6) — the route calling this does not change."""

from optimization_core.entities import SemanticValidationResult


def validate(original_text: str, optimized_text: str) -> SemanticValidationResult:
    if original_text == optimized_text:
        return SemanticValidationResult(semantic_similarity=1.0, constraint_preservation=1.0, confidence=1.0)

    original_words = set(original_text.lower().split())
    optimized_words = set(optimized_text.lower().split())
    similarity = 1.0 if not original_words else len(original_words & optimized_words) / len(original_words)

    return SemanticValidationResult(
        semantic_similarity=similarity, constraint_preservation=similarity, confidence=similarity
    )
