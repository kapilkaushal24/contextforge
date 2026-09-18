"""Placeholder pipeline (Phase 5 skeleton): echoes the input text back unchanged.
Replaced strategy-by-strategy across Phases 6-9 (deterministic optimization,
structural/semantic compression, validation, per docs/architecture/ai-ml.md's
pipeline) — the request/response contract and layering established here does not
change; only what happens inside `run_stub_optimization` does.
"""

from optimization_core.entities import (
    OptimizationRequest,
    OptimizationResult,
    SemanticValidationResult,
)

from app.application.tokenize_use_case import estimate_tokens


def run_stub_optimization(request: OptimizationRequest) -> OptimizationResult:
    original_tokens = estimate_tokens(request.text)
    return OptimizationResult(
        original_text=request.text,
        optimized_text=request.text,
        original_tokens=original_tokens,
        optimized_tokens=original_tokens,
        optimization_mode=request.mode,
        validation=SemanticValidationResult(semantic_similarity=1.0, constraint_preservation=1.0, confidence=1.0),
        requires_review=False,
        changes=(),
    )
