"""Seat service for business logic."""
from typing import List
from sqlalchemy.orm import Session

from app.modules.seats.seat_repository import SeatRepository
from app.modules.seats.dto.seat_dto import (
    SeatResponse, SeatListResponse, SeatActionResponse
)
from app.models.seat import SeatStatus


class SeatService:
    """Service for seat operations."""

    def __init__(self, db: Session):
        self.db = db
        self.repository = SeatRepository(db)

    def _to_response(self, seat) -> SeatResponse:
        """Convert seat model to response DTO."""
        return SeatResponse(
            id=seat.id,
            showtime_id=seat.showtime_id,
            seat_label=seat.seat_label,
            status=seat.status,
        )

    def get_seats_for_showtime(self, showtime_id: int) -> SeatListResponse:
        """Get all seats for a showtime with their statuses."""
        seats = self.repository.get_by_showtime_id(showtime_id)
        return SeatListResponse(
            seats=[self._to_response(s) for s in seats],
            total=len(seats),
        )

    def hold_seats(self, seat_ids: List[int], showtime_id: int) -> SeatActionResponse:
        """Attempt to hold seats temporarily."""
        # Get current seat states
        seats = self.repository.get_by_ids(seat_ids)

        # Validate all seats exist and belong to this showtime
        if len(seats) != len(seat_ids):
            return SeatActionResponse(
                success=False,
                message="One or more seats not found",
                released_seats=[],
            )

        # Check all seats belong to the correct showtime
        for seat in seats:
            if seat.showtime_id != showtime_id:# type: ignore[arg-type]
                return SeatActionResponse(
                    success=False,
                    message=f"Seat {seat.seat_label} does not belong to this showtime",
                    released_seats=[],
                )

        # Check all seats are available
        available_seats = self.repository.get_available_seats(seat_ids)
        if len(available_seats) != len(seat_ids):
            unavailable = set(seat_ids) - {s.id for s in available_seats}
            return SeatActionResponse(
                success=False,
                message=f"Seats {unavailable} are not available",
                released_seats=[],
            )

        # Hold the seats
        held_seats = self.repository.update_status(seat_ids, SeatStatus.HELD)
        return SeatActionResponse(
            success=True,
            message=f"Successfully held {len(seat_ids)} seat(s)",
            released_seats=[self._to_response(s) for s in held_seats],
        )

    def release_seats(self, seat_ids: List[int], showtime_id: int) -> SeatActionResponse:
        """Release held seats back to available."""
        # Get current seat states
        seats = self.repository.get_by_ids(seat_ids)

        # Validate seats exist
        if len(seats) != len(seat_ids):
            return SeatActionResponse(
                success=False,
                message="One or more seats not found",
                released_seats=[],
            )

        # Check all seats belong to the correct showtime
        for seat in seats:
            if seat.showtime_id != showtime_id:# type: ignore[arg-type]
                return SeatActionResponse(
                    success=False,
                    message=f"Seat {seat.seat_label} does not belong to this showtime",
                    released_seats=[],
                )

        # Release the seats (set to available regardless of current status)
        released_seats = self.repository.update_status(seat_ids, SeatStatus.AVAILABLE)
        return SeatActionResponse(
            success=True,
            message=f"Successfully released {len(seat_ids)} seat(s)",
            released_seats=[self._to_response(s) for s in released_seats],
        )
