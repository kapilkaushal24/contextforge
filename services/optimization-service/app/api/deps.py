"""Composition root: where concrete tokenizers, providers, and the router are chosen and
injected. The rest of the app depends only on the domain interfaces."""

from functools import lru_cache
from typing import Any

from aito_providers import AnthropicProvider, OpenAIProvider
from aito_tokenizers import TokenizerRegistry
from optimization_core import HeuristicSemanticValidator, ModelRouter, RouterPolicy
from optimization_core.enums import TokenizerProvider
from optimization_core.interfaces import IAIProvider, ISemanticValidator, ITokenizer
from optimization_core.strategies import SemanticCompressionStrategy

from app.config.settings import Settings, get_settings

_open_providers: list[Any] = []


@lru_cache
def get_semantic_validator() -> ISemanticValidator:
    return HeuristicSemanticValidator()


@lru_cache
def get_tokenizer_registry() -> TokenizerRegistry:
    return TokenizerRegistry()


def resolve_tokenizer_for_platform(
    platform: str, settings: Settings, registry: TokenizerRegistry
) -> ITokenizer:
    """Platform ids are open strings (ADR-009): the platform->tokenizer mapping is
    configuration, and any unmapped platform uses the generic tokenizer."""
    provider = settings.platform_tokenizer_map.get(platform, TokenizerProvider.GENERIC.value)
    return registry.get(TokenizerProvider(provider))


def build_provider(settings: Settings) -> IAIProvider | None:
    """None unless LLM optimization is enabled and a key is configured."""
    if not settings.enable_llm_optimization or settings.llm_api_key is None:
        return None
    key = settings.llm_api_key.get_secret_value()
    if settings.llm_provider == "openai":
        return OpenAIProvider(key, settings.llm_model, timeout=settings.llm_timeout_seconds)
    if settings.llm_provider == "anthropic":
        return AnthropicProvider(key, settings.llm_model, timeout=settings.llm_timeout_seconds)
    raise ValueError(f"unsupported AITO_LLM_PROVIDER: {settings.llm_provider!r}")


@lru_cache
def get_model_router() -> ModelRouter:
    settings = get_settings()
    provider = build_provider(settings)
    if provider is not None:
        _open_providers.append(provider)
    semantic = SemanticCompressionStrategy(provider) if provider else None
    return ModelRouter(
        semantic,
        RouterPolicy(
            llm_enabled=settings.enable_llm_optimization,
            cost_optimization_enabled=settings.cost_optimization_enabled,
            optimizer_input_price_per_1k=settings.llm_input_price_per_1k_usd,
            optimizer_output_price_per_1k=settings.llm_output_price_per_1k_usd,
            downstream_input_price_per_1k=settings.input_price_per_1k_usd,
        ),
    )


async def close_providers() -> None:
    """Called at app shutdown to release provider HTTP connections."""
    for provider in _open_providers:
        close = getattr(provider, "aclose", None)
        if close is not None:
            await close()
    _open_providers.clear()
    get_model_router.cache_clear()
