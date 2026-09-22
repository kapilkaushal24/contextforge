from typing import Annotated

from fastapi import APIRouter, Depends
from optimization_core.interfaces import ISemanticValidator

from app.api.deps import get_semantic_validator
from app.api.v1.schemas import SemanticValidationResult, ValidateRequest

router = APIRouter(tags=["validate"])


@router.post("/validate", response_model=SemanticValidationResult)
async def validate(
    payload: ValidateRequest,
    validator: Annotated[ISemanticValidator, Depends(get_semantic_validator)],
) -> SemanticValidationResult:
    result = validator.validate(payload.original_text, payload.optimized_text)
    return SemanticValidationResult(
        semantic_similarity=result.semantic_similarity,
        constraint_preservation=result.constraint_preservation,
        confidence=result.confidence,
        issues=list(result.issues),
    )
