"""Optimization use case. Phase 6: runs the deterministic strategy (no LLM) and
validates the result. Token counting and validation are still the Phase 5
placeholders (real ones land in Phases 7 and 9) — swapping them touches only the
imported helpers, not this flow.
"""

from optimization_core.entities import OptimizationRequest, OptimizationResult
from optimization_core.strategies import DeterministicCompressionStrategy

from app.application.tokenize_use_case import estimate_tokens
from app.application.validate_use_case import validate


def run_optimization(request: OptimizationRequest, confidence_threshold: float) -> OptimizationResult:
    strategy = DeterministicCompressionStrategy(request.mode)
    optimized_text, changes = strategy.optimize(request.text)

    validation = validate(request.text, optimized_text)
    return OptimizationResult(
        original_text=request.text,
        optimized_text=optimized_text,
        original_tokens=estimate_tokens(request.text),
        optimized_tokens=estimate_tokens(optimized_text),
        optimization_mode=request.mode,
        validation=validation,
        requires_review=validation.confidence < confidence_threshold,
        changes=tuple(changes),
    )
