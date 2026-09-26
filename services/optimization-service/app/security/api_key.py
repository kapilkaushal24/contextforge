"""API-key auth, applied to every /api/v1 route (see app/api/v1/router.py). Off by
default in dev (`AITO_REQUIRE_API_KEY=false`) so local development needs no setup;
enterprise/production deployments turn it on. This is the auth-ready wiring point
MVP scope item 11 calls for — full OAuth2/OIDC is a later phase (docs/security/
privacy-security.md §3)."""

from typing import Annotated

from fastapi import Depends, Header, HTTPException, status

from app.config.settings import Settings, get_settings


async def require_api_key(
    settings: Annotated[Settings, Depends(get_settings)],
    x_api_key: Annotated[str | None, Header()] = None,
) -> None:
    if not settings.require_api_key:
        return
    if not settings.api_key or x_api_key != settings.api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or missing API key"
        )
