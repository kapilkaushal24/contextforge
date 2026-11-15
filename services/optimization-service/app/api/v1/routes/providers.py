"""Expose configured provider and model metadata without revealing credentials."""

from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.v1.schemas import ModelInfo, ProviderInfo
from app.config.settings import Settings, get_settings

router = APIRouter(tags=["providers"])


@router.get("/providers", response_model=list[ProviderInfo])
async def list_providers(
    settings: Annotated[Settings, Depends(get_settings)],
) -> list[ProviderInfo]:
    configured = (
        settings.enable_llm_optimization
        and settings.llm_api_key is not None
        and bool(settings.llm_api_key.get_secret_value())
    )
    return [
        ProviderInfo(
            id=provider_id,
            name=name,
            status=(
                "available"
                if configured and settings.llm_provider == provider_id
                else "unavailable"
            ),
        )
        for provider_id, name in (("openai", "OpenAI"), ("anthropic", "Anthropic"))
    ]


@router.get("/models", response_model=list[ModelInfo])
async def list_models(
    settings: Annotated[Settings, Depends(get_settings)],
) -> list[ModelInfo]:
    return [
        ModelInfo(
            id=settings.llm_model,
            provider_id=settings.llm_provider,
            name=settings.llm_model,
            input_price_per_1k=settings.llm_input_price_per_1k_usd,
            output_price_per_1k=settings.llm_output_price_per_1k_usd,
        )
    ]
