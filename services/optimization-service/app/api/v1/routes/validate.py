from fastapi import APIRouter

from app.api.v1.schemas import SemanticValidationResult, ValidateRequest
from app.application.validate_use_case import validate as run_validation

router = APIRouter(tags=["validate"])


@router.post("/validate", response_model=SemanticValidationResult)
async def validate(payload: ValidateRequest) -> SemanticValidationResult:
    result = run_validation(payload.original_text, payload.optimized_text)
    return SemanticValidationResult(
        semantic_similarity=result.semantic_similarity,
        constraint_preservation=result.constraint_preservation,
        confidence=result.confidence,
    )
