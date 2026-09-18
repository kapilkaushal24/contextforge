"""In-memory settings only — no user/org model or DB wired up yet (that lands with
auth in a later phase). Fine for a single-process dev skeleton; not durable."""

from fastapi import APIRouter

from app.api.v1.schemas import UserSettings

router = APIRouter(tags=["settings"])

_settings_store = UserSettings()


@router.get("/settings", response_model=UserSettings)
async def get_settings_endpoint() -> UserSettings:
    return _settings_store


@router.put("/settings", response_model=UserSettings)
async def put_settings_endpoint(payload: UserSettings) -> UserSettings:
    global _settings_store
    _settings_store = payload
    return _settings_store
