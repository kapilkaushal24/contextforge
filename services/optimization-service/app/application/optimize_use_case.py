"""Optimization pipeline (docs/architecture/ai-ml.md §1), cheapest safe transformation first:

    deterministic (A) -> structural (B) -> [router gate] -> semantic LLM (F) -> validate

The router decides whether the LLM step runs (privacy, mode, cost, and — Phase 11 —
detected sensitive content). An LLM failure never blocks the user: the
deterministic/structural result is returned instead. The result is scored by the
injected `ISemanticValidator`; a score below the confidence threshold sets requires_review.

Phase 12 observability: each stage's wall-clock time is logged as a single structured
"pipeline stage timings" line per request (correlated by request_id via the logging
middleware) rather than one log line per stage — cheap, greppable, and enough to answer
"where did this request's latency go" without standing up a tracing backend. Prometheus
metrics (app/observability/metrics.py) capture the aggregate numbers for dashboards/alerts.
"""

import logging
import time

from optimization_core.classifier import RuleBasedContentAnalyzer
from optimization_core.entities import OptimizationChange, OptimizationRequest, OptimizationResult
from optimization_core.errors import ProviderError
from optimization_core.interfaces import IModelRouter, ISemanticValidator, ITokenizer
from optimization_core.pii import detect_pii
from optimization_core.strategies import (
    DeterministicCompressionStrategy,
    StructuralOptimizationStrategy,
)

from app.application.tokenize_use_case import count_tokens, estimate_input_cost_usd
from app.observability.metrics import (
    llm_latency_seconds,
    llm_requests_total,
    optimize_latency_seconds,
    optimize_requests_total,
    semantic_validation_failures_total,
    token_reduction_percentage,
)

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
    pipeline_started = time.perf_counter()
    stage_ms: dict[str, float] = {}

    prompt_type = _analyzer.classify(request.text)
    text = request.text
    changes: list[OptimizationChange] = []

    stage_started = time.perf_counter()
    text, step_changes = await DeterministicCompressionStrategy(request.mode).optimize(text)
    changes += step_changes
    stage_ms["deterministic"] = _elapsed_ms(stage_started)

    structural = StructuralOptimizationStrategy()
    if structural.applies_to(prompt_type, request.mode):
        stage_started = time.perf_counter()
        text, step_changes = await structural.optimize(text)
        changes += step_changes
        stage_ms["structural"] = _elapsed_ms(stage_started)

    # Detected once here (not inside the router) so the categories can also be
    # surfaced in the response — never the matched text itself, only the category
    # names (docs/security/privacy-security.md §1).
    sensitive_categories = tuple(m.category for m in detect_pii(request.text))

    decision = router.route(
        request,
        prompt_type,
        count_tokens(text, tokenizer),
        contains_sensitive_content=bool(sensitive_categories),
    )
    logger.info(
        "llm routing decision",
        extra={"routing_reason": decision.reason, "sensitive_categories": sensitive_categories},
    )
    if decision.strategy is not None:
        stage_started = time.perf_counter()
        try:
            text, step_changes = await decision.strategy.optimize(text)
            changes += step_changes
            llm_requests_total.labels(outcome="success").inc()
        except ProviderError as exc:
            # Never block the user's workflow on an LLM failure (error-handling principle).
            logger.warning("llm optimization unavailable", extra={"error": str(exc)})
            llm_requests_total.labels(outcome="error").inc()
        finally:
            llm_stage_ms = _elapsed_ms(stage_started)
            stage_ms["llm"] = llm_stage_ms
            llm_latency_seconds.observe(llm_stage_ms / 1000)

    stage_started = time.perf_counter()
    original_tokens = count_tokens(request.text, tokenizer)
    optimized_tokens = count_tokens(text, tokenizer)
    validation = validator.validate(request.text, text)
    stage_ms["validation"] = _elapsed_ms(stage_started)

    requires_review = validation.confidence < confidence_threshold
    result = OptimizationResult(
        original_text=request.text,
        optimized_text=text,
        original_tokens=original_tokens,
        optimized_tokens=optimized_tokens,
        optimization_mode=request.mode,
        validation=validation,
        requires_review=requires_review,
        changes=tuple(changes),
        estimated_cost_saved=estimate_input_cost_usd(
            max(0, original_tokens - optimized_tokens), input_price_per_1k_usd
        ),
        sensitive_categories=sensitive_categories,
    )

    total_ms = _elapsed_ms(pipeline_started)
    mode_label = request.mode.value
    optimize_requests_total.labels(mode=mode_label, outcome="success").inc()
    optimize_latency_seconds.labels(mode=mode_label).observe(total_ms / 1000)
    token_reduction_percentage.observe(result.reduction_percentage)
    if requires_review:
        semantic_validation_failures_total.inc()

    logger.info(
        "optimize pipeline stage timings",
        extra={"stage_ms": stage_ms, "total_ms": total_ms, "requires_review": requires_review},
    )
    return result


def _elapsed_ms(started_at: float) -> float:
    return (time.perf_counter() - started_at) * 1000
