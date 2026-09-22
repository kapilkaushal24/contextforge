"""Semantic validator (ISemanticValidator) — docs/architecture/ai-ml.md §6.

Deterministic, local, and explainable: it never calls a model, so validating an
optimization costs nothing and leaks nothing. It cannot *understand* text; it measures
whether the things that carry a prompt's meaning survived, and reports a score plus the
reasons for any loss.

- constraint_preservation: retention of what must not be lost, weighted by severity.
  Hard (weight 2): fenced code, numbers, identifiers, quoted literals/examples, negations.
  Soft (weight 1): constraint words (must/at most/...), output-format terms, named entities.
  Content the optimizer *introduced* (new numbers/identifiers/quotes) is penalized.
- semantic_similarity: recall-weighted F-score over stemmed content words, ignoring
  politeness/function words — so removing "could you please" or a duplicate sentence is
  free, while dropping real topic words is not.
- confidence: 0.6 * constraint + 0.4 * similarity, capped at 0.5 whenever any hard item
  was lost — so a dropped "not" or number can never be waved through by high word overlap.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable

from optimization_core.entities import SemanticValidationResult
from optimization_core.features import Features, extract

_HARD_WEIGHT = 2
_SOFT_WEIGHT = 1
_BETA_SQUARED = 4.0  # recall counts 4x precision: losing content is worse than adding some
_MIN_HARD_LOSS_CAP = 0.5
_INTRODUCED_PENALTY_EACH = 0.1
_INTRODUCED_PENALTY_MAX = 0.4


def _lost(items: Iterable[str], present: Callable[[str], bool]) -> list[str]:
    return [item for item in items if not present(item)]


class HeuristicSemanticValidator:
    def validate(self, original_text: str, optimized_text: str) -> SemanticValidationResult:
        if original_text == optimized_text:
            return SemanticValidationResult(1.0, 1.0, 1.0)
        if not optimized_text.strip():
            return SemanticValidationResult(0.0, 0.0, 0.0, issues=("empty_output",))

        o, c = extract(original_text), extract(optimized_text)
        constraint, issues, hard_lost = self._constraint_preservation(o, c)
        similarity = self._similarity(o, c)

        confidence = 0.6 * constraint + 0.4 * similarity
        if hard_lost:
            confidence = min(confidence, _MIN_HARD_LOSS_CAP)
        return SemanticValidationResult(
            semantic_similarity=similarity,
            constraint_preservation=constraint,
            confidence=max(0.0, min(1.0, confidence)),
            issues=tuple(issues),
        )

    @staticmethod
    def _constraint_preservation(o: Features, c: Features) -> tuple[float, list[str], bool]:
        c_prose_lower = c.prose.casefold()
        hard = {
            "fenced_code": _lost(o.fenced_blocks, lambda x: x in c.raw),
            "numbers": _lost(o.numbers, lambda x: x in c.numbers),
            "identifiers": _lost(o.identifiers, lambda x: x in c.prose),
            "quoted_literals": _lost(o.quoted_literals, lambda x: x in c.prose),
            "negations": _lost(o.negations, lambda x: x in c.negations),
        }
        soft = {
            "constraint_words": _lost(o.constraint_markers, lambda x: x in c.constraint_markers),
            "format_terms": _lost(o.format_terms, lambda x: x in c.format_terms),
            "entities": _lost(o.entities, lambda x: x.casefold() in c_prose_lower),
        }
        totals = {
            "fenced_code": len(o.fenced_blocks),
            "numbers": len(o.numbers),
            "identifiers": len(o.identifiers),
            "quoted_literals": len(o.quoted_literals),
            "negations": len(o.negations),
            "constraint_words": len(o.constraint_markers),
            "format_terms": len(o.format_terms),
            "entities": len(o.entities),
        }

        total_weight = retained_weight = 0
        issues: list[str] = []
        for group, weight in ((hard, _HARD_WEIGHT), (soft, _SOFT_WEIGHT)):
            for name, lost in group.items():
                total_weight += totals[name] * weight
                retained_weight += (totals[name] - len(lost)) * weight
                if lost:
                    issues.append(f"missing_{name}")

        retention = 1.0 if total_weight == 0 else retained_weight / total_weight

        introduced = (
            len(c.numbers - o.numbers)
            + len(_lost(c.quoted_literals, lambda x: x in o.prose))
            + len(_lost(c.identifiers, lambda x: x in o.prose))
        )
        if introduced:
            issues.append("introduced_content")
        penalty = min(_INTRODUCED_PENALTY_MAX, _INTRODUCED_PENALTY_EACH * introduced)
        hard_lost = any(hard.values())
        return max(0.0, retention - penalty), issues, hard_lost

    @staticmethod
    def _similarity(o: Features, c: Features) -> float:
        if not o.content_words and not c.content_words:
            return 1.0
        if not o.content_words or not c.content_words:
            return 0.0
        shared = len(o.content_words & c.content_words)
        recall = shared / len(o.content_words)
        precision = shared / len(c.content_words)
        if shared == 0:
            return 0.0
        return (1 + _BETA_SQUARED) * precision * recall / (_BETA_SQUARED * precision + recall)
