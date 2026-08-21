"""Seat API endpoints with Redis distributed locking."""
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.modules.seats.seat_service import SeatService
from app.modules.seats.dto.seat_dto import (
    SeatListResponse,
    HoldSeatsRequest,
    ReleaseSeatsRequest,
    ExtendHoldRequest,
    SeatActionResponse,
    HoldExpiryResponse,
    HoldStatusResponse,
)
from app.shared.db.database import get_db
from app.shared.redis import get_redis
from app.modules.auth.auth_controller import get_current_user_id
import redis.asyncio as redis

router = APIRouter(prefix="/api/v1", tags=["seats"])


def get_seat_service(
    db: Session = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis),
) -> SeatService:
    """Dependency to get seat service with Redis."""
    return SeatService(db, redis_client)


@router.get("/showtimes/{showtime_id}/seats", response_model=SeatListResponse)
def get_showtime_seats(
    showtime_id: int,
    service: SeatService = Depends(get_seat_service),
):
    """
    Get all seats for a specific showtime with their current status.

    - **showtime_id**: The ID of the showtime
    """
    return service.get_seats_for_showtime(showtime_id)


@router.post(
    "/seats/hold",
    response_model=SeatActionResponse,
)
async def hold_seats(
    request: HoldSeatsRequest,
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    service: SeatService = Depends(get_seat_service),
):
    """
    Hold seats temporarily for a showtime.

    Requires authentication. Seats will be locked for 10 minutes
    (configurable via SEAT_HOLD_TTL) to allow time for payment.

    - **seat_ids**: List of seat IDs to hold
    - **showtime_id**: The showtime these seats belong to

    Returns failure if any seat is already held by another user.
    """
    return await service.hold_seats(
        seat_ids=request.seat_ids,
        showtime_id=request.showtime_id,
        user_id=user_id,
    )


@router.post(
    "/seats/release",
    response_model=SeatActionResponse,
)
async def release_seats(
    request: ReleaseSeatsRequest,
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    service: SeatService = Depends(get_seat_service),
):
    """
    Release held seats back to available status.

    Requires authentication. Only releases seats that are held by you.

    - **seat_ids**: List of seat IDs to release
    - **showtime_id**: The showtime these seats belong to
    """
    return await service.release_seats(
        seat_ids=request.seat_ids,
        showtime_id=request.showtime_id,
        user_id=user_id,
    )


@router.post(
    "/seats/extend",
    response_model=HoldExpiryResponse,
)
async def extend_hold(
    request: ExtendHoldRequest,
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    service: SeatService = Depends(get_seat_service),
):
    """
    Extend the hold duration for seats.

    Requires authentication. Only extends holds owned by you.

    - **seat_ids**: List of seat IDs to extend
    - **showtime_id**: The showtime these seats belong to
    - **extra_seconds**: Additional seconds to add (default: 300 = 5 minutes)
    """
    return await service.extend_hold(
        seat_ids=request.seat_ids,
        showtime_id=request.showtime_id,
        user_id=user_id,
        extra_seconds=request.extra_seconds or 300,
    )


@router.get(
    "/seats/status",
    response_model=HoldStatusResponse,
)
async def check_hold_status(
    seat_ids: list[int],
    showtime_id: int,
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    service: SeatService = Depends(get_seat_service),
):
    """
    Check hold status for seats.

    Requires authentication. Returns info about which seats are held
    and by whom, plus remaining TTL for your holds.

    - **seat_ids**: List of seat IDs to check
    - **showtime_id**: The showtime these seats belong to
    """
    return await service.check_hold_status(
        seat_ids=seat_ids,
        showtime_id=showtime_id,
        user_id=user_id,
    )
