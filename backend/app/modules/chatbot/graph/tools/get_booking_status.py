"""Get booking status tool."""
from typing import Annotated

from langchain_core.tools import tool


@tool
def get_booking_status(
    booking_code: Annotated[str, "Booking code to check"],
) -> dict:
    """
    Check the status of a booking.

    Args:
        booking_code: The booking code

    Returns:
        Dict with booking details and status
    """
    from sqlalchemy import select
    from app.models.booking import Booking
    from app.models.film import Film
    from app.models.showtime import Showtime
    from app.shared.db.database import SessionLocal

    db = SessionLocal()
    try:
        booking = db.execute(
            select(Booking).where(Booking.booking_code == booking_code)
        ).scalar_one_or_none()

        if not booking:
            return {"found": False, "message": "Booking not found"}

        # Get film info
        showtime = db.get(Showtime, booking.showtime_id)
        film_title = "Unknown"
        if showtime:
            film = db.get(Film, showtime.film_id)
            if film:
                film_title = film.title

        status_emoji = {
            "PENDING": "⏳",
            "CONFIRMED": "✅",
            "CANCELLED": "❌",
        }

        return {
            "found": True,
            "booking_code": booking.booking_code,
            "film_title": film_title,
            "status": booking.status.value,
            "status_emoji": status_emoji.get(booking.status.value, "❓"),
            "total_price": booking.total_price,
            "created_at": booking.created_at.isoformat(),
        }
    finally:
        db.close()
