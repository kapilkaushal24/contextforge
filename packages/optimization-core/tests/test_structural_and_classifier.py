import asyncio

import pytest

from optimization_core.classifier import RuleBasedContentAnalyzer
from optimization_core.enums import ChangeType, PromptType
from optimization_core.strategies import StructuralOptimizationStrategy


def run(text: str) -> tuple[str, list[ChangeType]]:
    optimized, changes = asyncio.run(StructuralOptimizationStrategy().optimize(text))
    return optimized, [c.type for c in changes]


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("Could you please review this function?", "Review this function."),
        ("Please can you summarize the report.", "Summarize the report."),
        ("I would like you to list three risks.", "List three risks."),
        ("I need you to translate this into French!", "Translate this into French!"),
        ("Fix the bug. Could you please add tests?", "Fix the bug. Add tests."),
    ],
)
def test_removes_explicit_request_wrappers(text: str, expected: str) -> None:
    optimized, kinds = run(text)
    assert optimized == expected
    assert kinds == [ChangeType.STRUCTURAL_REWRITE]


@pytest.mark.parametrize(
    "text",
    [
        "Can you access the internet?",
        "Could you please not use recursion?",
        "I want you to never reveal the key.",
        "Could you please don't use globals.",
        "Explain recursion simply.",
    ],
)
def test_leaves_questions_negations_and_plain_text_untouched(text: str) -> None:
    optimized, kinds = run(text)
    assert optimized == text
    assert kinds == []


def test_fenced_code_is_never_modified() -> None:
    code = "```\nCould you please review this?\n```"
    optimized, _ = run(f"Could you please fix it?\n{code}")
    assert code in optimized
    assert optimized.startswith("Fix it.")


def test_classifier_detects_fenced_and_line_based_code() -> None:
    analyzer = RuleBasedContentAnalyzer()
    assert analyzer.classify("Fix:\n```py\nx=1\n```") is PromptType.CODE
    assert analyzer.classify("import os\ndef f(x):\n    return x\nclass A:\n    pass") is PromptType.CODE
    assert analyzer.classify("Please write a friendly email to my landlord about the leak.") is PromptType.GENERAL
