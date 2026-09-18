from fastapi import APIRouter

from app.api.v1.schemas import AnalyzeRequest, AnalyzeResult
from app.application.analyze_use_case import analyze as run_analysis

router = APIRouter(tags=["analyze"])


@router.post("/analyze", response_model=AnalyzeResult)
async def analyze(payload: AnalyzeRequest) -> AnalyzeResult:
    result = run_analysis(payload.text)
    return AnalyzeResult(
        prompt_type=result.prompt_type,
        estimated_tokens=result.estimated_tokens,
        has_detected_redundancy=result.has_detected_redundancy,
    )
