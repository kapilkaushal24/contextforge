import asyncio

import pytest

from optimization_core.enums import ChangeType, OptimizationMode
from optimization_core.interfaces import IOptimizationStrategy
from optimization_core.strategies import DeterministicCompressionStrategy


def run(
    text: str, mode: OptimizationMode = OptimizationMode.BALANCED
) -> tuple[str, set[ChangeType]]:
    optimized, changes = asyncio.run(DeterministicCompressionStrategy(mode).optimize(text))
    return optimized, {c.type for c in changes}


def test_satisfies_strategy_protocol() -> None:
    assert isinstance(DeterministicCompressionStrategy(), IOptimizationStrategy)
    assert DeterministicCompressionStrategy().requires_llm_call is False


def test_collapses_whitespace() -> None:
    optimized, kinds = run("Review   this    code.\n\n\n\n\nThanks.   ")
    assert optimized == "Review this code.\n\nThanks."
    assert ChangeType.WHITESPACE_CLEANUP in kinds


def test_removes_exact_duplicate_sentence_keeps_first() -> None:
    text = "Use PostgreSQL for the database. Add tests. Use PostgreSQL for the database."
    optimized, kinds = run(text)
    assert optimized == "Use PostgreSQL for the database. Add tests."
    assert ChangeType.DEDUPLICATION in kinds


def test_dedupes_across_case_and_punctuation() -> None:
    optimized, _ = run("Always return JSON output.\nalways return json output!")
    assert optimized == "Always return JSON output."


def test_conservative_keeps_duplicate_sentences_on_one_line() -> None:
    text = "Use PostgreSQL for the database. Add tests. Use PostgreSQL for the database."
    optimized, _ = run(text, OptimizationMode.CONSERVATIVE)
    assert optimized == text


def test_short_repeats_are_never_removed() -> None:
    text = "Yes.   Do not.\nYes.   Do not."
    optimized, _ = run(text)
    assert optimized.count("Yes.") == 2 and optimized.count("Do not.") == 2


def test_different_numbers_are_not_duplicates() -> None:
    text = "Limit the response to 100 words please.\nLimit the response to 200 words please."
    optimized, _ = run(text)
    assert optimized == text


def test_code_blocks_are_never_modified() -> None:
    code = "```python\nx  =  1\n\n\n\nx  =  1\nprint('a b c d')\nprint('a b c d')\n```"
    text = f"Fix this   bug.\n\n{code}\n\nFix this   bug."
    optimized, _ = run(text)
    assert code in optimized
    assert optimized.count("Fix this bug.") == 1


def test_boilerplate_only_removed_in_aggressive() -> None:
    text = "Summarize the report in three bullet points. Thanks in advance!"
    balanced, _ = run(text, OptimizationMode.BALANCED)
    aggressive, kinds = run(text, OptimizationMode.AGGRESSIVE)
    assert balanced == text
    assert aggressive == "Summarize the report in three bullet points."
    assert ChangeType.BOILERPLATE_REMOVAL in kinds


@pytest.mark.parametrize("mode", list(OptimizationMode))
def test_idempotent_and_never_longer(mode: OptimizationMode) -> None:
    text = "Do this now please.   Do this now please.\n\n\n\nThen do that.  Thanks in advance."
    once, _ = run(text, mode)
    twice, _ = run(once, mode)
    assert len(once) <= len(text)
    assert twice == once


def test_already_minimal_text_is_returned_unchanged_with_no_changes() -> None:
    text = "Explain recursion simply."
    optimized, kinds = run(text)
    assert optimized == text
    assert kinds == set()
