"""Booking service for business logic."""
import secrets
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.modules.bookings.booking_repository import BookingRepository# type: ignore[arg-type]
from app.modules.bookings.dto.booking_dto import (# type: ignore[arg-type]
    CreateBookingRequest,
    BookingResponse,
    BookingListResponse,
    BookingActionResponse,
)# type: ignore[arg-type]
from app.modules.seats.seat_repository import SeatRepository
from app.modules.showtimes.showtime_repository import ShowtimeRepository
from app.models.booking import Booking, BookingStatus
from app.models.seat import SeatStatus


class BookingService:
    """Service for booking operations."""

    # Booking expires after 10 minutes if not paid
    DEFAULT_EXPIRY_MINUTES = 10

    def __init__(self, db: Session):
        self.db = db
        self.repository = BookingRepository(db)
        self.seat_repository = SeatRepository(db)
        self.showtime_repository = ShowtimeRepository(db)

    def _generate_booking_code(self) -> str:
        """Generate a unique booking code."""
        # Format: CBNK + 6 random alphanumeric chars (e.g., CBNK7X9M2P)
        chars = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
        suffix = "".join(secrets.choice(chars) for _ in range(6))
        return f"CBNK{suffix}"

    def _to_response(self, booking: Booking) -> BookingResponse:
        """Convert booking model to response DTO."""
        seats = []
        for bs in booking.booking_seats:
            seats.append({
                "id": bs.seat.id,
                "showtime_id": bs.seat.showtime_id,
                "seat_label": bs.seat.seat_label,
                "status": bs.seat.status,
            })

        return BookingResponse(
            id=booking.id,
            user_id=str(booking.user_id),
            showtime_id=booking.showtime_id,
            booking_code=booking.booking_code,
            total_price=Decimal(str(booking.total_price)),
            status=booking.status,
            expires_at=booking.expires_at,
            cancelled_at=booking.cancelled_at,
            cancellation_reason=booking.cancellation_reason,
            created_at=booking.created_at,
            updated_at=booking.updated_at,
            seats=seats,  # type: ignore[arg-value]
        )

    def create_booking(
        self,
        user_id: UUID,
        request: CreateBookingRequest,
    ) -> BookingActionResponse:
        """
        Create a new booking from held seats.

        Flow:
        1. Validate showtime exists
        2. Validate all seats exist and are held by this user
        3. Calculate total price
        4. Create booking with PENDING status
        5. Keep seats in HELD status until payment confirmed
        """
        # Validate showtime exists
        showtime = self.showtime_repository.get_by_id(request.showtime_id)
        if not showtime:
            return BookingActionResponse(
                success=False,
                message="Showtime not found",
                booking=None,
            )

        # Validate all seats exist
        seats = self.seat_repository.get_by_ids(request.seat_ids)
        if len(seats) != len(request.seat_ids):
            return BookingActionResponse(
                success=False,
                message="One or more seats not found",
                booking=None,
            )

        # Validate all seats belong to the correct showtime
        for seat in seats:
            if seat.showtime_id != request.showtime_id:
                return BookingActionResponse(
                    success=False,
                    message=f"Seat {seat.seat_label} does not belong to this showtime",
                    booking=None,
                )

        # Validate all seats are in HELD status (user must have called hold first)
        held_seats = [s for s in seats if s.status == SeatStatus.HELD]
        if len(held_seats) != len(seats):
            unavailable = [s.seat_label for s in seats if s.status != SeatStatus.HELD]
            return BookingActionResponse(
                success=False,
                message=f"Seats {unavailable} are not in held status. Please hold seats first.",
                booking=None,
            )

        # Calculate total price (base price * number of seats)
        total_price = float(showtime.base_price) * len(seats)

        # Generate unique booking code
        booking_code = self._generate_booking_code()
        while self.repository.get_by_booking_code(booking_code):
            booking_code = self._generate_booking_code()

        # Set expiry time
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=self.DEFAULT_EXPIRY_MINUTES)

        # Create booking
        booking = self.repository.create(
            user_id=user_id,
            showtime_id=request.showtime_id,
            booking_code=booking_code,
            total_price=total_price,
            seat_ids=request.seat_ids,
            expires_at=expires_at,
        )

        return BookingActionResponse(
            success=True,
            message=f"Booking created successfully. Code: {booking_code}",
            booking=self._to_response(booking),
        )

    def get_booking(self, booking_id: int, user_id: UUID) -> Optional[BookingResponse]:
        """Get a booking by ID for a specific user."""
        booking = self.repository.get_by_id(booking_id)
        if not booking:
            return None

        # Ensure user owns this booking
        if booking.user_id != user_id:
            return None

        return self._to_response(booking)

    def get_user_bookings(
        self,
        user_id: UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> BookingListResponse:
        """Get all bookings for a user."""
        bookings, total = self.repository.get_by_user_id(user_id, skip, limit)
        return BookingListResponse(
            bookings=[self._to_response(b) for b in bookings],
            total=total,
        )

    def cancel_booking(
        self,
        booking_id: int,
        user_id: UUID,
        reason: Optional[str] = None,
    ) -> BookingActionResponse:
        """
        Cancel a booking.

        Flow:
        1. Validate booking exists and belongs to user
        2. Validate booking is in PENDING status
        3. Update booking status to CANCELLED
        4. Release all seats back to AVAILABLE
        """
        booking = self.repository.get_by_id(booking_id)
        if not booking:
            return BookingActionResponse(
                success=False,
                message="Booking not found",
                booking=None,
            )

        # Ensure user owns this booking
        if booking.user_id != user_id:
            return BookingActionResponse(
                success=False,
                message="You don't have permission to cancel this booking",
                booking=None,
            )

        # Can only cancel PENDING bookings
        if booking.status != BookingStatus.PENDING:
            return BookingActionResponse(
                success=False,
                message=f"Cannot cancel booking with status {booking.status.value}",
                booking=None,
            )

        # Get seat IDs to release
        seat_ids = [bs.seat_id for bs in booking.booking_seats]

        # Cancel the booking
        cancelled_booking = self.repository.cancel(booking_id, reason)

        # Release the seats back to available
        self.seat_repository.update_status(seat_ids, SeatStatus.AVAILABLE)

        return BookingActionResponse(
            success=True,
            message="Booking cancelled successfully. Seats have been released.",
            booking=self._to_response(cancelled_booking),  # type: ignore[arg-value]
        )

    def confirm_booking(self, booking_id: int) -> Optional[BookingResponse]:
        """
        Confirm a booking after successful payment.

        Flow:
        1. Validate booking exists and is PENDING
        2. Validate booking has not expired
        3. Update booking status to CONFIRMED
        4. Update seats to BOOKED status
        """
        booking = self.repository.get_by_id(booking_id)
        if not booking:
            return None

        # Can only confirm PENDING bookings
        if booking.status != BookingStatus.PENDING:
            return None

        # Check if booking has expired
        if booking.expires_at and booking.expires_at < datetime.now(timezone.utc):
            # Auto-cancel expired booking
            self.cancel_booking(booking_id, booking.user_id, "Booking expired")
            return None

        # Get seat IDs
        seat_ids = [bs.seat_id for bs in booking.booking_seats]

        # Confirm the booking
        confirmed_booking = self.repository.confirm(booking_id)

        # Update seats to BOOKED
        self.seat_repository.update_status(seat_ids, SeatStatus.BOOKED)

        return self._to_response(confirmed_booking)  # type: ignore[return-value]

    def expire_pending_bookings(self) -> int:
        """
        Find and expire all pending bookings that have passed their expiry time.
        Returns the number of bookings expired.
        """
        expired_bookings = self.repository.get_pending_expired()
        count = 0

        for booking in expired_bookings:
            seat_ids = [bs.seat_id for bs in booking.booking_seats]
            self.repository.cancel(booking.id, "Booking expired - payment timeout")
            self.seat_repository.update_status(seat_ids, SeatStatus.AVAILABLE)
            count += 1

        return count
