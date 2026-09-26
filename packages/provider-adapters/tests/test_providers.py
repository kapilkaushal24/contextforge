import json

import httpx
import pytest
from optimization_core.errors import ProviderError
from optimization_core.interfaces import IAIProvider

from aito_providers import AnthropicProvider, OpenAIProvider

SECRET = "sk-super-secret"


def mock(status: int = 200, payload: object = None, exc: Exception | None = None):  # type: ignore[no-untyped-def]
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        if exc:
            raise exc
        return httpx.Response(status, json=payload)

    return httpx.AsyncClient(transport=httpx.MockTransport(handler)), seen


def mock_raw_body(status: int, body: bytes) -> httpx.AsyncClient:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(status, content=body)

    return httpx.AsyncClient(transport=httpx.MockTransport(handler))


async def test_openai_sends_system_and_user_in_separate_roles() -> None:
    http, seen = mock(payload={"choices": [{"message": {"content": "short"}}]})
    provider = OpenAIProvider(SECRET, "gpt-x", client=http)
    assert isinstance(provider, IAIProvider)

    assert await provider.complete(system="RULES", user="DATA", max_tokens=50) == "short"

    request = seen[0]
    body = json.loads(request.content)
    assert str(request.url) == "https://api.openai.com/v1/chat/completions"
    assert request.headers["authorization"] == f"Bearer {SECRET}"
    assert body["messages"] == [
        {"role": "system", "content": "RULES"},
        {"role": "user", "content": "DATA"},
    ]
    assert body["max_completion_tokens"] == 50 and body["model"] == "gpt-x"


async def test_anthropic_uses_top_level_system_field() -> None:
    http, seen = mock(payload={"content": [{"type": "text", "text": "short"}]})
    provider = AnthropicProvider(SECRET, "claude-x", client=http)
    assert isinstance(provider, IAIProvider)

    assert await provider.complete(system="RULES", user="DATA", max_tokens=50) == "short"

    request = seen[0]
    body = json.loads(request.content)
    assert str(request.url) == "https://api.anthropic.com/v1/messages"
    assert request.headers["x-api-key"] == SECRET
    assert request.headers["anthropic-version"] == "2023-06-01"
    assert body["system"] == "RULES"
    assert body["messages"] == [{"role": "user", "content": "DATA"}]


@pytest.mark.parametrize("cls", [OpenAIProvider, AnthropicProvider])
@pytest.mark.parametrize("status", [401, 429, 500])
async def test_http_errors_become_provider_error_without_leaking_secrets(cls, status) -> None:  # type: ignore[no-untyped-def]
    http, _ = mock(status=status, payload={"error": f"bad key {SECRET} and prompt DATA"})
    with pytest.raises(ProviderError) as info:
        await cls(SECRET, "m", client=http).complete(system="s", user="DATA", max_tokens=5)
    assert SECRET not in str(info.value) and "DATA" not in str(info.value)
    assert str(status) in str(info.value)


@pytest.mark.parametrize("cls", [OpenAIProvider, AnthropicProvider])
async def test_timeouts_and_network_errors_become_provider_error(cls) -> None:  # type: ignore[no-untyped-def]
    for exc in (httpx.ReadTimeout("t"), httpx.ConnectError("c")):
        http, _ = mock(exc=exc)
        with pytest.raises(ProviderError):
            await cls(SECRET, "m", client=http).complete(system="s", user="u", max_tokens=5)


@pytest.mark.parametrize("cls", [OpenAIProvider, AnthropicProvider])
@pytest.mark.parametrize("payload", [{}, {"choices": []}, {"content": None}, []])
async def test_malformed_responses_become_provider_error(cls, payload) -> None:  # type: ignore[no-untyped-def]
    http, _ = mock(payload=payload)
    with pytest.raises(ProviderError):
        await cls(SECRET, "m", client=http).complete(system="s", user="u", max_tokens=5)


@pytest.mark.parametrize("cls", [OpenAIProvider, AnthropicProvider])
async def test_2xx_response_with_non_json_body_becomes_provider_error(cls) -> None:  # type: ignore[no-untyped-def]
    http = mock_raw_body(200, b"<html>not json</html>")
    with pytest.raises(ProviderError, match="invalid JSON"):
        await cls(SECRET, "m", client=http).complete(system="s", user="u", max_tokens=5)


async def test_openai_non_string_content_becomes_provider_error() -> None:
    # Content present and well-formed but not text (e.g. a tool-call/array shape) must
    # not be silently coerced — the caller expects a plain string.
    http, _ = mock(payload={"choices": [{"message": {"content": ["not", "a", "string"]}}]})
    with pytest.raises(ProviderError, match="not text"):
        await OpenAIProvider(SECRET, "m", client=http).complete(system="s", user="u", max_tokens=5)


@pytest.mark.parametrize("cls", [OpenAIProvider, AnthropicProvider])
async def test_aclose_closes_the_underlying_http_client(cls) -> None:  # type: ignore[no-untyped-def]
    http, _ = mock(payload={})
    provider = cls(SECRET, "m", client=http)
    assert http.is_closed is False
    await provider.aclose()
    assert http.is_closed is True
