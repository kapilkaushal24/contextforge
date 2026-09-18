"""No analytics rollup table is wired up yet (Phase 15) — returns an honest zeroed
summary for the requested range rather than fabricated numbers."""

from datetime import UTC, date, datetime, timedelta

from fastapi import APIRouter, Query

from app.api.v1.schemas import UsageSummary

router = APIRouter(tags=["usage"])


def _default_range_start() -> date:
    return datetime.now(tz=UTC).date() - timedelta(days=7)


def _default_range_end() -> date:
    return datetime.now(tz=UTC).date()


@router.get("/usage", response_model=UsageSummary)
async def get_usage(
    range_start: date = Query(default_factory=_default_range_start),
    range_end: date = Query(default_factory=_default_range_end),
) -> UsageSummary:
    return UsageSummary(
        range_start=range_start.isoformat(),
        range_end=range_end.isoformat(),
        total_requests=0,
        total_tokens_saved=0,
        average_reduction_percentage=0.0,
        estimated_cost_saved=0.0,
    )
