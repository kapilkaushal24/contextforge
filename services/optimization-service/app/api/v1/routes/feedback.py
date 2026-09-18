"""Accepts feedback and logs it (never used for model training without explicit
consent — docs/product/requirements.md §7). No persistence store wired up yet."""

import logging

from fastapi import APIRouter, status

from app.api.v1.schemas import FeedbackAck, FeedbackRequest

router = APIRouter(tags=["feedback"])
logger = logging.getLogger(__name__)


@router.post("/feedback", response_model=FeedbackAck, status_code=status.HTTP_202_ACCEPTED)
async def submit_feedback(payload: FeedbackRequest) -> FeedbackAck:
    logger.info(
        "feedback received",
        extra={"request_id": payload.request_id, "rating": payload.rating, "reason": payload.reason},
    )
    return FeedbackAck(accepted=True)
