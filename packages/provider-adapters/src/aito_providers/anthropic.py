from __future__ import annotations

import httpx
from optimization_core.errors import ProviderError

from aito_providers.http import DEFAULT_TIMEOUT_SECONDS, post_json

ANTHROPIC_MESSAGES_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_VERSION = "2023-06-01"


class AnthropicProvider:
    provider_id = "anthropic"

    def __init__(
        self,
        api_key: str,
        model: str,
        *,
        client: httpx.AsyncClient | None = None,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
    ) -> None:
        self._api_key = api_key
        self._model = model
        self._client = client or httpx.AsyncClient(timeout=timeout)

    async def complete(self, *, system: str, user: str, max_tokens: int) -> str:
        data = await post_json(
            self._client,
            ANTHROPIC_MESSAGES_URL,
            headers={"x-api-key": self._api_key, "anthropic-version": ANTHROPIC_VERSION},
            body={
                "model": self._model,
                "max_tokens": max_tokens,
                "system": system,
                "messages": [{"role": "user", "content": user}],
            },
        )
        try:
            text = "".join(
                block["text"] for block in data["content"] if block.get("type") == "text"
            )
        except (KeyError, TypeError, AttributeError) as exc:
            raise ProviderError("provider response missing text content") from exc
        return text

    async def aclose(self) -> None:
        await self._client.aclose()
