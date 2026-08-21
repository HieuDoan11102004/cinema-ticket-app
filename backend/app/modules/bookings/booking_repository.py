"""Booking repository for database operations."""
from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, and_, func
from sqlalchemy.orm import Session, joinedload

from app.models.booking import Booking, BookingSeat, BookingStatus
from app.models.seat import Seat, SeatStatus


class BookingRepository:
    """Repository for Booking database operations."""

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, booking_id: int) -> Optional[Booking]:
        """Get booking by ID with seats and showtime loaded."""
        stmt = (
            select(Booking)
            .options(
                joinedload(Booking.booking_seats).joinedload(BookingSeat.seat),
                joinedload(Booking.showtime)
            )
            .where(Booking.id == booking_id)
        )
        return self.db.scalars(stmt).first()

    def get_by_user_id(
        self,
        user_id: UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[List[Booking], int]:
        """Get all bookings for a user."""
        conditions = [Booking.user_id == user_id]

        stmt = (
            select(Booking)
            .options(
                joinedload(Booking.booking_seats).joinedload(BookingSeat.seat),
                joinedload(Booking.showtime)
            )
            .where(and_(*conditions))
            .order_by(Booking.created_at.desc())
        )

        # Get total count
        count_stmt = select(func.count(Booking.id)).where(and_(*conditions))
        total = self.db.scalar(count_stmt) or 0

        # Apply pagination
        stmt = stmt.offset(skip).limit(limit)
        bookings = list(self.db.scalars(stmt).all())

        return bookings, total

    def get_by_booking_code(self, booking_code: str) -> Optional[Booking]:
        """Get booking by its unique booking code."""
        stmt = (
            select(Booking)
            .options(
                joinedload(Booking.booking_seats).joinedload(BookingSeat.seat),
                joinedload(Booking.showtime)
            )
            .where(Booking.booking_code == booking_code)
        )
        return self.db.scalars(stmt).first()

    def get_pending_expired(self) -> List[Booking]:
        """Get all pending bookings that have expired."""
        stmt = (
            select(Booking)
            .options(
                joinedload(Booking.booking_seats).joinedload(BookingSeat.seat)
            )
            .where(
                and_(
                    Booking.status == BookingStatus.PENDING,
                    Booking.expires_at < datetime.now(timezone.utc)
                )
            )
        )
        return list(self.db.scalars(stmt).all())

    def create(
        self,
        user_id: UUID,
        showtime_id: int,
        booking_code: str,
        total_price: float,
        seat_ids: List[int],
        expires_at: Optional[datetime] = None,
    ) -> Booking:
        """Create a new booking with associated seat reservations."""
        booking = Booking(
            user_id=user_id,
            showtime_id=showtime_id,
            booking_code=booking_code,
            total_price=total_price,
            status=BookingStatus.PENDING,
            expires_at=expires_at,
        )
        self.db.add(booking)
        self.db.flush()  # Get the booking ID

        # Create booking_seat associations
        for seat_id in seat_ids:
            booking_seat = BookingSeat(
                booking_id=booking.id,
                seat_id=seat_id
            )
            self.db.add(booking_seat)

        self.db.commit()
        self.db.refresh(booking)
        return booking

    def update_status(
        self,
        booking_id: int,
        status: BookingStatus,
        cancellation_reason: Optional[str] = None,
    ) -> Optional[Booking]:
        """Update booking status."""
        booking = self.get_by_id(booking_id)
        if not booking:
            return None

        booking.status = status# type: ignore[arg-type]
        if status == BookingStatus.CANCELLED:
            booking.cancelled_at = datetime.now(timezone.utc)# type: ignore[arg-type]
            booking.cancellation_reason = cancellation_reason# type: ignore[arg-type]

        self.db.commit()
        self.db.refresh(booking)
        return booking

    def confirm(self, booking_id: int) -> Optional[Booking]:
        """Confirm a booking (payment successful)."""
        return self.update_status(booking_id, BookingStatus.CONFIRMED)

    def cancel(
        self,
        booking_id: int,
        cancellation_reason: Optional[str] = None,
    ) -> Optional[Booking]:
        """Cancel a booking."""
        return self.update_status(booking_id, BookingStatus.CANCELLED, cancellation_reason)
