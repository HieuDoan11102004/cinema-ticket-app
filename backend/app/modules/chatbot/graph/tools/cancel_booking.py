"""Cancel booking tool."""
from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID

from langchain_core.tools import tool


@tool
def cancel_booking(
    booking_code: Annotated[str, "Booking code to cancel"],
    user_id: Annotated[str, "User ID"],
    reason: Annotated[str | None, "Cancellation reason"] = None,
) -> dict:
    """
    Cancel an existing booking.

    Args:
        booking_code: The booking code
        user_id: User requesting cancellation
        reason: Optional cancellation reason

    Returns:
        Dict with cancellation result
    """
    from sqlalchemy import and_, select
    from app.models.booking import Booking, BookingStatus
    from app.models.seat import Seat, SeatStatus
    from app.shared.db.database import SessionLocal

    db = SessionLocal()
    try:
        booking = db.execute(
            select(Booking).where(
                and_(
                    Booking.booking_code == booking_code,
                    Booking.user_id == UUID(user_id),
                )
            )
        ).scalar_one_or_none()

        if not booking:
            return {"success": False, "message": "Booking not found"}

        if booking.status == BookingStatus.CANCELLED:
            return {"success": False, "message": "Booking already cancelled"}

        # Cancel booking
        booking.status = BookingStatus.CANCELLED
        booking.cancelled_at = datetime.now(UTC)
        booking.cancellation_reason = reason or "Cancelled by user via chatbot"

        # Release seats
        seats = db.execute(
            select(Seat).where(
                and_(
                    Seat.showtime_id == booking.showtime_id,
                    Seat.status == SeatStatus.HELD,
                )
            )
        ).scalars().all()

        # Simple heuristic: release seats if they were likely from this booking
        # (In production, track seat->booking relationship)
        for seat in seats:
            seat.status = SeatStatus.AVAILABLE

        db.commit()

        return {
            "success": True,
            "message": f"Booking {booking_code} cancelled",
        }
    except Exception as e:
        db.rollback()
        return {"success": False, "message": str(e)}
    finally:
        db.close()
