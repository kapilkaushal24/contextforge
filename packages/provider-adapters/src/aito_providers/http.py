"""Shared HTTP plumbing. Base URLs are fixed constants per provider (SSRF: no
user-controlled URLs). Errors are mapped to `ProviderError` with messages that never
include the request body, response body, or credentials."""

from __future__ import annotations

from typing import Any

import httpx
from optimization_core.errors import ProviderError

DEFAULT_TIMEOUT_SECONDS = 20.0


async def post_json(
    client: httpx.AsyncClient, url: str, *, headers: dict[str, str], body: dict[str, Any]
) -> dict[str, Any]:
    try:
        response = await client.post(url, headers=headers, json=body)
    except httpx.TimeoutException as exc:
        raise ProviderError("provider request timed out") from exc
    except httpx.HTTPError as exc:
        raise ProviderError(f"provider request failed: {type(exc).__name__}") from exc

    if response.status_code >= 400:
        raise ProviderError(f"provider returned HTTP {response.status_code}")
    try:
        data = response.json()
    except ValueError as exc:
        raise ProviderError("provider returned invalid JSON") from exc
    if not isinstance(data, dict):
        raise ProviderError("provider returned an unexpected response shape")
    return data
