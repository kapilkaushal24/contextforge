from fastapi import APIRouter

from app.api.v1.schemas import EstimateTokensRequest, EstimateTokensResponse
from app.application.tokenize_use_case import estimate_tokens

router = APIRouter(tags=["tokens"])


@router.post("/estimate-tokens", response_model=EstimateTokensResponse)
async def estimate_tokens_endpoint(payload: EstimateTokensRequest) -> EstimateTokensResponse:
    return EstimateTokensResponse(tokens=estimate_tokens(payload.text), provider=payload.provider, method="estimated")
