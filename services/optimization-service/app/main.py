from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Response
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.deps import close_providers
from app.api.errors import (
    ApiException,
    api_exception_handler,
    http_exception_handler,
    unhandled_exception_handler,
    validation_exception_handler,
)
from app.api.v1.router import router as v1_router
from app.config.settings import get_settings
from app.observability.logging import configure_logging
from app.observability.metrics import METRICS_CONTENT_TYPE, render_metrics
from app.observability.middleware import RequestIdMiddleware


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    yield
    await close_providers()


def create_app() -> FastAPI:
    configure_logging()
    settings = get_settings()

    app = FastAPI(
        lifespan=lifespan,
        title="AI Token Optimizer API",
        version="0.1.0",
        description="Phase 5 skeleton — routing, DTOs, and layering are real; "
        "optimization logic is placeholder until Phases 6-9 land.",
    )

    app.add_middleware(RequestIdMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allow_origins,
        allow_methods=["GET", "POST", "PUT"],
        allow_headers=["Content-Type", "X-API-Key", "X-Request-ID"],
    )

    app.add_exception_handler(ApiException, api_exception_handler)  # type: ignore[arg-type]
    app.add_exception_handler(RequestValidationError, validation_exception_handler)  # type: ignore[arg-type]
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)  # type: ignore[arg-type]
    app.add_exception_handler(Exception, unhandled_exception_handler)

    app.include_router(v1_router)

    @app.get("/healthz", tags=["health"])
    async def healthz() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/metrics", tags=["observability"])
    async def metrics() -> Response:
        # Outside /api/v1 and never gated by the API key (§12: monitoring/scraping
        # needs its own network-level access control, not the app's request auth).
        return Response(content=render_metrics(), media_type=METRICS_CONTENT_TYPE)

    return app


app = create_app()
