import asyncio

import pytest

from optimization_core.enums import OptimizationMode
from optimization_core.interfaces import ISemanticValidator
from optimization_core.strategies import (
    DeterministicCompressionStrategy,
    StructuralOptimizationStrategy,
)
from optimization_core.validator import HeuristicSemanticValidator

V = HeuristicSemanticValidator()
THRESHOLD = 0.85

LONG = (
    "Could you please write a Python function called parse_config that reads a YAML file "
    'and must not use eval? It should return at most 10 keys and log "config loaded" once.'
)


def test_satisfies_protocol() -> None:
    assert isinstance(V, ISemanticValidator)


def test_identical_text_is_perfect() -> None:
    r = V.validate(LONG, LONG)
    assert (r.semantic_similarity, r.constraint_preservation, r.confidence) == (1.0, 1.0, 1.0)
    assert r.issues == ()


def test_empty_output_is_zero() -> None:
    r = V.validate(LONG, "   ")
    assert r.confidence == 0.0 and r.issues == ("empty_output",)


@pytest.mark.parametrize(
    ("original", "optimized"),
    [
        (
            "Could you please review this function? Use PostgreSQL.   Use PostgreSQL.",
            "Review this function. Use PostgreSQL. Use PostgreSQL.",
        ),
        (
            "Use PostgreSQL for the database. Add tests. Use PostgreSQL for the database.",
            "Use PostgreSQL for the database. Add tests.",
        ),
        ("Summarize the report in three bullet points. Thanks in advance!", "Summarize the report in three bullet points."),
    ],
)
def test_harmless_edits_are_not_flagged_for_review(original: str, optimized: str) -> None:
    r = V.validate(original, optimized)
    assert r.confidence >= THRESHOLD, r
    assert r.issues == ()


def test_the_real_strategy_outputs_never_trip_review_on_typical_prompts() -> None:
    prompts = [
        "Could you please review this function? Use PostgreSQL. Use PostgreSQL.",
        "I would like you to list three risks.   List three risks with mitigation steps.",
        "Fix the login bug.   Fix the login bug.\n\n\n\nThanks in advance!",
    ]
    for text in prompts:
        out, _ = asyncio.run(DeterministicCompressionStrategy(OptimizationMode.AGGRESSIVE).optimize(text))
        out, _ = asyncio.run(StructuralOptimizationStrategy().optimize(out))
        assert V.validate(text, out).confidence >= THRESHOLD, (text, out)


def test_good_llm_style_rewrite_passes() -> None:
    rewrite = 'Write Python parse_config: read YAML, must not use eval, return at most 10 keys, log "config loaded" once.'
    r = V.validate(LONG, rewrite)
    # "It should return" -> imperative "return" drops the modal "should": a soft,
    # informational loss that must not, on its own, trigger review.
    assert r.confidence >= THRESHOLD
    assert set(r.issues) <= {"missing_constraint_words"}


@pytest.mark.parametrize(
    ("rewrite", "issue"),
    [
        ("Write Python parse_config: read YAML, use eval, return at most 10 keys, log \"config loaded\" once.", "missing_negations"),
        ("Write Python parse_config: read YAML, must not use eval, return at most 20 keys, log \"config loaded\" once.", "missing_numbers"),
        ("Write Python parse_config: read YAML, must not use eval, return at most 10 keys, log once.", "missing_quoted_literals"),
        ("Write Python load_settings: read YAML, must not use eval, return at most 10 keys, log \"config loaded\" once.", "missing_identifiers"),
    ],
)
def test_dropping_a_hard_constraint_forces_review_despite_high_word_overlap(rewrite: str, issue: str) -> None:
    r = V.validate(LONG, rewrite)
    assert issue in r.issues
    assert r.semantic_similarity > 0.7  # words mostly match...
    assert r.confidence <= 0.5 < THRESHOLD  # ...but it must still be flagged


def test_dropped_fenced_code_forces_review() -> None:
    original = "Fix this bug.\n```py\nx = 1\n```"
    r = V.validate(original, "Fix this bug.\n```py\nx = 2\n```")
    assert "missing_fenced_code" in r.issues and r.confidence <= 0.5


def test_soft_losses_reduce_the_score_without_hard_cap() -> None:
    original = "Return the result as JSON. It must include the user ID and Postgres status."
    r = V.validate(original, "Return the user ID and status.")
    assert {"missing_format_terms", "missing_constraint_words"} <= set(r.issues)
    assert r.confidence < THRESHOLD


def test_introduced_numbers_are_penalized() -> None:
    r = V.validate("Write a short poem about autumn leaves falling.", "Write a 500 word poem about autumn leaves.")
    assert "introduced_content" in r.issues
    assert r.constraint_preservation < 1.0


def test_unrelated_text_scores_low_similarity() -> None:
    r = V.validate("Explain how photosynthesis works in plants.", "Recommend a good pasta recipe for dinner.")
    assert r.semantic_similarity < 0.2 and r.confidence < THRESHOLD


def test_scores_are_always_within_unit_interval() -> None:
    for a, b in [(LONG, "x"), ("a b c", "a b c d e f g h 1 2 3"), ("`x` 1 2 3 not", "y")]:
        r = V.validate(a, b)
        for score in (r.semantic_similarity, r.constraint_preservation, r.confidence):
            assert 0.0 <= score <= 1.0
