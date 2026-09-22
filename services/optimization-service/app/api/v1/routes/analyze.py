from typing import Annotated

from aito_tokenizers import TokenizerRegistry
from fastapi import APIRouter, Depends
from optimization_core.enums import TokenizerProvider

from app.api.deps import get_tokenizer_registry
from app.api.v1.schemas import AnalyzeRequest, AnalyzeResult
from app.application.analyze_use_case import analyze as run_analysis

router = APIRouter(tags=["analyze"])


@router.post("/analyze", response_model=AnalyzeResult)
async def analyze(
    payload: AnalyzeRequest,
    registry: Annotated[TokenizerRegistry, Depends(get_tokenizer_registry)],
) -> AnalyzeResult:
    result = run_analysis(payload.text, registry.get(TokenizerProvider.GENERIC))
    return AnalyzeResult(
        prompt_type=result.prompt_type,
        estimated_tokens=result.estimated_tokens,
        has_detected_redundancy=result.has_detected_redundancy,
    )
