from fastapi import APIRouter, Depends

from app.api.v1.routes import (
    analyze,
    feedback,
    optimize,
    providers,
    settings,
    tokens,
    usage,
    validate,
)
from app.security.api_key import require_api_key

# Every /api/v1 route requires the API key when AITO_REQUIRE_API_KEY=true (off by
# default in dev — see app/security/api_key.py).
router = APIRouter(prefix="/api/v1", dependencies=[Depends(require_api_key)])

router.include_router(optimize.router)
router.include_router(analyze.router)
router.include_router(tokens.router)
router.include_router(validate.router)
router.include_router(providers.router)
router.include_router(usage.router)
router.include_router(settings.router)
router.include_router(feedback.router)
