import pytest
from aito_providers import AnthropicProvider, OpenAIProvider
from fastapi.testclient import TestClient
from pydantic import SecretStr

import app.api.deps as deps_module
from app.api.deps import build_provider, close_providers, get_model_router
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


async def test_close_providers_calls_aclose_on_every_registered_provider() -> None:
    class RecordingProvider:
        provider_id = "recording"

        def __init__(self) -> None:
            self.closed = False

        async def complete(self, *, system: str, user: str, max_tokens: int) -> str:
            return ""

        async def aclose(self) -> None:
            self.closed = True

    fake = RecordingProvider()
    deps_module._open_providers.append(fake)
    try:
        await close_providers()
        assert fake.closed is True
        assert deps_module._open_providers == []
    finally:
        if fake in deps_module._open_providers:
            deps_module._open_providers.remove(fake)


def test_get_model_router_registers_a_real_provider_for_close_on_shutdown(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # get_model_router() calls the module-level get_settings() directly (not via
    # FastAPI's Depends), so exercising the "LLM enabled" composition-root path means
    # patching that reference rather than using app.dependency_overrides.
    llm_settings = Settings(
        _env_file=None,  # type: ignore[call-arg]
        enable_llm_optimization=True,
        llm_api_key=SecretStr("k"),
        llm_provider="openai",
    )
    monkeypatch.setattr(deps_module, "get_settings", lambda: llm_settings)
    get_model_router.cache_clear()
    before = list(deps_module._open_providers)

    try:
        router = get_model_router()
        assert len(deps_module._open_providers) == len(before) + 1
        assert router is not None
    finally:
        for provider in deps_module._open_providers[len(before) :]:
            deps_module._open_providers.remove(provider)
        get_model_router.cache_clear()
