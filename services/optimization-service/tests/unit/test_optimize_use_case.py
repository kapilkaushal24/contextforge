from optimization_core.entities import OptimizationRequest
from optimization_core.enums import OptimizationMode, PrivacyPolicy

from app.application.optimize_use_case import run_stub_optimization
from app.application.tokenize_use_case import estimate_tokens


def test_stub_optimization_echoes_text_unchanged() -> None:
    request = OptimizationRequest(
        text="Please review this code for bugs.",
        platform="chatgpt",
        mode=OptimizationMode.BALANCED,
        privacy_policy=PrivacyPolicy.CLOUD_ALLOWED,
    )

    result = run_stub_optimization(request)

    assert result.optimized_text == request.text
    assert result.tokens_saved == 0
    assert result.requires_review is False
    assert result.confidence == 1.0


def test_estimate_tokens_is_deterministic_and_positive() -> None:
    assert estimate_tokens("a") == 1
    assert estimate_tokens("a" * 40) == 10
    assert estimate_tokens("") == 1
