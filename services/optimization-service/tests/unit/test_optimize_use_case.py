from optimization_core.entities import OptimizationRequest
from optimization_core.enums import ChangeType, OptimizationMode, PrivacyPolicy

from app.application.optimize_use_case import run_optimization
from app.application.tokenize_use_case import estimate_tokens


def make_request(text: str, mode: OptimizationMode = OptimizationMode.BALANCED) -> OptimizationRequest:
    return OptimizationRequest(
        text=text, platform="chatgpt", mode=mode, privacy_policy=PrivacyPolicy.CLOUD_ALLOWED
    )


def test_minimal_prompt_is_returned_unchanged() -> None:
    request = make_request("Please review this code for bugs.")

    result = run_optimization(request, confidence_threshold=0.85)

    assert result.optimized_text == request.text
    assert result.tokens_saved == 0
    assert result.changes == ()
    assert result.requires_review is False


def test_redundant_prompt_is_compressed_and_reports_changes() -> None:
    request = make_request(
        "Use PostgreSQL for the database.   Write unit tests.\n\n\n\n\nUse PostgreSQL for the database."
    )

    result = run_optimization(request, confidence_threshold=0.85)

    assert result.optimized_text == "Use PostgreSQL for the database. Write unit tests."
    assert result.tokens_saved > 0
    assert {c.type for c in result.changes} == {ChangeType.DEDUPLICATION, ChangeType.WHITESPACE_CLEANUP}
    assert result.requires_review is False


def test_low_confidence_is_flagged_for_review() -> None:
    request = make_request("Repeat this exact sentence twice. Repeat this exact sentence twice.")

    result = run_optimization(request, confidence_threshold=1.1)

    assert result.requires_review is True


def test_estimate_tokens_is_deterministic_and_positive() -> None:
    assert estimate_tokens("a") == 1
    assert estimate_tokens("a" * 40) == 10
    assert estimate_tokens("") == 1
