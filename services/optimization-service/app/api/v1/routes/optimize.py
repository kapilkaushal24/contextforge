from typing import Annotated

from fastapi import APIRouter, Depends
from optimization_core.entities import OptimizationRequest
from optimization_core.enums import OptimizationMode, PrivacyPolicy

from app.api.v1.schemas import OptimizationChange, OptimizeRequest, OptimizeResult
from app.application.optimize_use_case import run_optimization
from app.config.settings import Settings, get_settings

router = APIRouter(tags=["optimize"])


@router.post("/optimize", response_model=OptimizeResult)
async def optimize(
    payload: OptimizeRequest, settings: Annotated[Settings, Depends(get_settings)]
) -> OptimizeResult:
    domain_request = OptimizationRequest(
        text=payload.text,
        platform=payload.platform,
        mode=OptimizationMode(payload.mode),
        privacy_policy=PrivacyPolicy(payload.privacy_policy),
        conversation_context=tuple(payload.conversation_context or ()),
    )
    result = run_optimization(domain_request, settings.semantic_confidence_threshold)

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
        requires_review=result.requires_review,
        changes=[
            OptimizationChange(type=c.type.value, description=c.description, impact=c.impact.value)
            for c in result.changes
        ],
    )
