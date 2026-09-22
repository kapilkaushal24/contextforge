"""Optimization pipeline (docs/architecture/ai-ml.md §1), cheapest safe transformation first:

    deterministic (A) -> structural (B) -> [router gate] -> semantic LLM (F) -> validate

The router decides whether the LLM step runs (privacy, mode, cost). An LLM failure never
blocks the user: the deterministic/structural result is returned instead. The result is scored by the
injected `ISemanticValidator`; a score below the confidence threshold sets requires_review.
"""

import logging

from optimization_core.classifier import RuleBasedContentAnalyzer
from optimization_core.entities import OptimizationChange, OptimizationRequest, OptimizationResult
from optimization_core.errors import ProviderError
from optimization_core.interfaces import IModelRouter, ISemanticValidator, ITokenizer
from optimization_core.strategies import (
    DeterministicCompressionStrategy,
    StructuralOptimizationStrategy,
)

from app.application.tokenize_use_case import count_tokens, estimate_input_cost_usd

logger = logging.getLogger(__name__)
_analyzer = RuleBasedContentAnalyzer()


async def run_optimization(
    request: OptimizationRequest,
    *,
    tokenizer: ITokenizer,
    router: IModelRouter,
    validator: ISemanticValidator,
    confidence_threshold: float,
    input_price_per_1k_usd: float,
) -> OptimizationResult:
    prompt_type = _analyzer.classify(request.text)
    text = request.text
    changes: list[OptimizationChange] = []

    text, step_changes = await DeterministicCompressionStrategy(request.mode).optimize(text)
    changes += step_changes

    structural = StructuralOptimizationStrategy()
    if structural.applies_to(prompt_type, request.mode):
        text, step_changes = await structural.optimize(text)
        changes += step_changes

    decision = router.route(request, prompt_type, count_tokens(text, tokenizer))
    logger.info("llm routing decision", extra={"routing_reason": decision.reason})
    if decision.strategy is not None:
        try:
            text, step_changes = await decision.strategy.optimize(text)
            changes += step_changes
        except ProviderError as exc:
            # Never block the user's workflow on an LLM failure (error-handling principle).
            logger.warning("llm optimization unavailable", extra={"error": str(exc)})

    original_tokens = count_tokens(request.text, tokenizer)
    optimized_tokens = count_tokens(text, tokenizer)
    validation = validator.validate(request.text, text)
    return OptimizationResult(
        original_text=request.text,
        optimized_text=text,
        original_tokens=original_tokens,
        optimized_tokens=optimized_tokens,
        optimization_mode=request.mode,
        validation=validation,
        requires_review=validation.confidence < confidence_threshold,
        changes=tuple(changes),
        estimated_cost_saved=estimate_input_cost_usd(
            max(0, original_tokens - optimized_tokens), input_price_per_1k_usd
        ),
    )
