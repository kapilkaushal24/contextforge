from __future__ import annotations

import httpx
from optimization_core.errors import ProviderError

from aito_providers.http import DEFAULT_TIMEOUT_SECONDS, post_json

OPENAI_CHAT_URL = "https://api.openai.com/v1/chat/completions"


class OpenAIProvider:
    provider_id = "openai"

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
            OPENAI_CHAT_URL,
            headers={"Authorization": f"Bearer {self._api_key}"},
            body={
                "model": self._model,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                "max_completion_tokens": max_tokens,
            },
        )
        try:
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise ProviderError("provider response missing message content") from exc
        if not isinstance(content, str):
            raise ProviderError("provider response content was not text")
        return content

    async def aclose(self) -> None:
        await self._client.aclose()
