from typing import Annotated

from aito_tokenizers import TokenizerRegistry
from fastapi import APIRouter, Depends
from optimization_core import ModelRouter
from optimization_core.entities import OptimizationRequest
from optimization_core.enums import OptimizationMode, PrivacyPolicy
from optimization_core.interfaces import ISemanticValidator

from app.api.deps import (
    get_model_router,
    get_semantic_validator,
    get_tokenizer_registry,
    resolve_tokenizer_for_platform,
)
from app.api.v1.schemas import OptimizationChange, OptimizeRequest, OptimizeResult
from app.application.optimize_use_case import run_optimization
from app.config.settings import Settings, get_settings

router = APIRouter(tags=["optimize"])


@router.post("/optimize", response_model=OptimizeResult)
async def optimize(
    payload: OptimizeRequest,
    settings: Annotated[Settings, Depends(get_settings)],
    registry: Annotated[TokenizerRegistry, Depends(get_tokenizer_registry)],
    router: Annotated[ModelRouter, Depends(get_model_router)],
    validator: Annotated[ISemanticValidator, Depends(get_semantic_validator)],
) -> OptimizeResult:
    domain_request = OptimizationRequest(
        text=payload.text,
        platform=payload.platform,
        mode=OptimizationMode(payload.mode),
        privacy_policy=PrivacyPolicy(payload.privacy_policy),
        conversation_context=tuple(payload.conversation_context or ()),
    )
    result = await run_optimization(
        domain_request,
        tokenizer=resolve_tokenizer_for_platform(payload.platform, settings, registry),
        router=router,
        validator=validator,
        confidence_threshold=settings.semantic_confidence_threshold,
        input_price_per_1k_usd=settings.input_price_per_1k_usd,
    )

    return OptimizeResult(
        original_text=result.original_text,
        optimized_text=result.optimized_text,
        original_tokens=result.original_tokens,
        optimized_tokens=result.optimized_tokens,
        tokens_saved=result.tokens_saved,
        reduction_percentage=result.reduction_percentage,
        estimated_cost_saved=result.estimated_cost_saved,
        optimization_mode=result.optimization_mode.value,
        confidence=result.confidence,
        semantic_similarity=result.validation.semantic_similarity,
        constraint_preservation=result.validation.constraint_preservation,
        review_reasons=list(result.validation.issues),
        requires_review=result.requires_review,
        changes=[
            OptimizationChange(type=c.type.value, description=c.description, impact=c.impact.value)
            for c in result.changes
        ],
        sensitive_content_categories=list(result.sensitive_categories),
    )
