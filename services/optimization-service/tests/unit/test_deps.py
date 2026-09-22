import pytest
from aito_providers import AnthropicProvider, OpenAIProvider
from fastapi.testclient import TestClient
from pydantic import SecretStr

from app.api.deps import build_provider, get_model_router
from app.config.settings import Settings
from app.main import create_app


def settings(**kwargs: object) -> Settings:
    return Settings(_env_file=None, **kwargs)  # type: ignore[call-arg, arg-type]


def test_no_provider_unless_enabled_and_keyed() -> None:
    assert build_provider(settings()) is None
    assert build_provider(settings(enable_llm_optimization=True)) is None
    assert build_provider(settings(llm_api_key=SecretStr("k"))) is None


def test_builds_configured_provider() -> None:
    on = {"enable_llm_optimization": True, "llm_api_key": SecretStr("k")}
    assert isinstance(build_provider(settings(**on)), OpenAIProvider)
    assert isinstance(build_provider(settings(llm_provider="anthropic", **on)), AnthropicProvider)


def test_rejects_unknown_provider() -> None:
    with pytest.raises(ValueError):
        build_provider(
            settings(enable_llm_optimization=True, llm_api_key=SecretStr("k"), llm_provider="nope")
        )


def test_api_key_is_not_exposed_in_settings_repr() -> None:
    assert "super-secret" not in repr(settings(llm_api_key=SecretStr("super-secret")))


def test_app_shutdown_closes_providers_and_resets_router_cache() -> None:
    get_model_router()
    with TestClient(create_app()):
        pass
    assert get_model_router.cache_info().currsize == 0
