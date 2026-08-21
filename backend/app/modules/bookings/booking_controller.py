"""Booking API endpoints with Redis integration."""
import uuid
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.modules.bookings.booking_service import BookingService
from app.modules.bookings.booking_repository import BookingRepository
from app.modules.bookings.dto.booking_dto import (
    CreateBookingRequest,
    BookingResponse,
    BookingListResponse,
    BookingActionResponse,
)
from app.modules.auth.auth_controller import get_current_user_id
from app.shared.db.database import get_db
from app.shared.redis import get_redis
import redis.asyncio as redis

router = APIRouter(prefix="/api/v1/bookings", tags=["bookings"])


class CancelBookingRequest(BaseModel):
    """Request to cancel a booking."""
    reason: Optional[str] = None


def get_booking_service(
    db: Session = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis),
) -> BookingService:
    """Dependency to get booking service with Redis."""
    return BookingService(db, redis_client)


@router.post(
    "",
    response_model=BookingActionResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": BookingActionResponse},
        401: {"description": "Not authenticated"},
    },
)
async def create_booking(
    request: CreateBookingRequest,
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    service: BookingService = Depends(get_booking_service),
) -> BookingActionResponse:
    """
    Create a new booking from held seats.

    The user must first hold seats using POST /api/v1/seats/hold before creating a booking.

    - **seat_ids**: List of seat IDs to book
    - **showtime_id**: The showtime these seats belong to

    Returns a booking with PENDING status. User must complete payment to confirm.
    """
    return await service.create_booking(user_id, request)


@router.get(
    "",
    response_model=BookingListResponse,
    responses={401: {"description": "Not authenticated"}},
)
def list_bookings(
    skip: int = 0,
    limit: int = 100,
    user_id: uuid.UUID = Depends(get_current_user_id),
    service: BookingService = Depends(get_booking_service),
) -> BookingListResponse:
    """
    Get all bookings for the current user.

    - **skip**: Number of bookings to skip (pagination)
    - **limit**: Maximum number of bookings to return
    """
    return service.get_user_bookings(user_id, skip, limit)


@router.get(
    "/{booking_id}",
    response_model=BookingResponse,
    responses={
        401: {"description": "Not authenticated"},
        404: {"description": "Booking not found"},
    },
)
def get_booking(
    booking_id: int,
    user_id: uuid.UUID = Depends(get_current_user_id),
    service: BookingService = Depends(get_booking_service),
) -> BookingResponse:
    """Get details of a specific booking."""
    booking = service.get_booking(booking_id, user_id)
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found or you don't have permission to view it",
        )
    return booking


@router.post(
    "/{booking_id}/cancel",
    response_model=BookingActionResponse,
    responses={
        400: {"model": BookingActionResponse},
        401: {"description": "Not authenticated"},
        404: {"description": "Booking not found"},
    },
)
async def cancel_booking(
    booking_id: int,
    request: Optional[CancelBookingRequest] = None,
    user_id: uuid.UUID = Depends(get_current_user_id),
    service: BookingService = Depends(get_booking_service),
) -> BookingActionResponse:
    """
    Cancel a pending booking.

    This will release all seats back to available status.

    - **booking_id**: The ID of the booking to cancel
    - **reason**: Optional reason for cancellation
    """
    reason = request.reason if request else None
    return await service.cancel_booking(booking_id, user_id, reason)
