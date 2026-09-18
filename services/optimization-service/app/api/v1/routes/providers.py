"""No `IAIProvider` adapters are wired up yet (Phase 8) — these return an honest empty
list rather than fabricated provider/pricing data."""

from fastapi import APIRouter

from app.api.v1.schemas import ModelInfo, ProviderInfo

router = APIRouter(tags=["providers"])


@router.get("/providers", response_model=list[ProviderInfo])
async def list_providers() -> list[ProviderInfo]:
    return []


@router.get("/models", response_model=list[ModelInfo])
async def list_models() -> list[ModelInfo]:
    return []
