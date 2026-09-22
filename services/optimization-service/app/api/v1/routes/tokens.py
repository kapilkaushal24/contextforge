from typing import Annotated

from aito_tokenizers import TokenizerRegistry
from fastapi import APIRouter, Depends
from optimization_core.enums import TokenizerProvider

from app.api.deps import get_tokenizer_registry
from app.api.v1.schemas import EstimateTokensRequest, EstimateTokensResponse
from app.application.tokenize_use_case import count_tokens

router = APIRouter(tags=["tokens"])


@router.post("/estimate-tokens", response_model=EstimateTokensResponse)
async def estimate_tokens_endpoint(
    payload: EstimateTokensRequest,
    registry: Annotated[TokenizerRegistry, Depends(get_tokenizer_registry)],
) -> EstimateTokensResponse:
    tokenizer = registry.get(TokenizerProvider(payload.provider))
    # Always "estimated": a local count, never a provider-reported billing figure.
    return EstimateTokensResponse(
        tokens=count_tokens(payload.text, tokenizer), provider=payload.provider, method="estimated"
    )
