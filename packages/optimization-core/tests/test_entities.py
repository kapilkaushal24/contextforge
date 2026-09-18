import pytest

from optimization_core.entities import (
    OptimizationChange,
    OptimizationRequest,
    OptimizationResult,
    SemanticValidationResult,
)
from optimization_core.enums import ChangeImpact, ChangeType, OptimizationMode, PrivacyPolicy


def test_optimization_request_rejects_empty_text() -> None:
    with pytest.raises(ValueError):
        OptimizationRequest(
            text="   ",
            platform="chatgpt",
            mode=OptimizationMode.BALANCED,
            privacy_policy=PrivacyPolicy.CLOUD_ALLOWED,
        )


def test_optimization_request_rejects_oversized_text() -> None:
    with pytest.raises(ValueError):
        OptimizationRequest(
            text="x" * 100_001,
            platform="chatgpt",
            mode=OptimizationMode.BALANCED,
            privacy_policy=PrivacyPolicy.CLOUD_ALLOWED,
        )


def test_semantic_validation_result_rejects_out_of_range_score() -> None:
    with pytest.raises(ValueError):
        SemanticValidationResult(semantic_similarity=1.5, constraint_preservation=0.9, confidence=0.9)


def test_optimization_result_computes_derived_fields() -> None:
    result = OptimizationResult(
        original_text="a" * 100,
        optimized_text="a" * 60,
        original_tokens=100,
        optimized_tokens=60,
        optimization_mode=OptimizationMode.BALANCED,
        validation=SemanticValidationResult(
            semantic_similarity=0.95, constraint_preservation=0.97, confidence=0.96
        ),
        requires_review=False,
        changes=(
            OptimizationChange(
                type=ChangeType.DEDUPLICATION,
                description="Removed repeated requirement",
                impact=ChangeImpact.LOW,
            ),
        ),
    )

    assert result.tokens_saved == 40
    assert result.reduction_percentage == 40.0
    assert result.confidence == 0.96


def test_optimization_result_reduction_percentage_handles_zero_original_tokens() -> None:
    result = OptimizationResult(
        original_text="",
        optimized_text="",
        original_tokens=0,
        optimized_tokens=0,
        optimization_mode=OptimizationMode.BALANCED,
        validation=SemanticValidationResult(
            semantic_similarity=1.0, constraint_preservation=1.0, confidence=1.0
        ),
        requires_review=False,
    )

    assert result.reduction_percentage == 0.0
