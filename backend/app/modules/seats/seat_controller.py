"""Seat API endpoints."""
from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.modules.seats.seat_service import SeatService
from app.modules.seats.dto.seat_dto import (
    SeatListResponse, HoldSeatsRequest, ReleaseSeatsRequest, SeatActionResponse
)
from app.shared.db.database import get_db

router = APIRouter(prefix="/api/v1", tags=["seats"])


def get_seat_service(db: Session = Depends(get_db)) -> SeatService:
    """Dependency to get seat service."""
    return SeatService(db)


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


@router.post("/seats/hold", response_model=SeatActionResponse)
def hold_seats(
    request: HoldSeatsRequest,
    service: SeatService = Depends(get_seat_service),
):
    """
    Hold seats temporarily for a showtime.
    Seats will be marked as HELD to prevent others from booking them.

    - **seat_ids**: List of seat IDs to hold
    - **showtime_id**: The showtime these seats belong to
    """
    return service.hold_seats(request.seat_ids, request.showtime_id)


@router.post("/seats/release", response_model=SeatActionResponse)
def release_seats(
    request: ReleaseSeatsRequest,
    service: SeatService = Depends(get_seat_service),
):
    """
    Release held seats back to available status.

    - **seat_ids**: List of seat IDs to release
    - **showtime_id**: The showtime these seats belong to
    """
    return service.release_seats(request.seat_ids, request.showtime_id)
