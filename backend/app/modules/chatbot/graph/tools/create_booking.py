"""Create booking tool."""
from typing import Annotated
from uuid import uuid4

from langchain_core.tools import tool


@tool
def create_booking(
    showtime_id: Annotated[int, "Showtime ID to book"],
    seat_labels: Annotated[list[str], "List of seat labels like ['A5', 'A6']"],
    user_id: Annotated[str, "User ID"],
) -> dict:
    """
    Create a booking for selected seats.

    This is a critical action - only call after user has confirmed:
    1. The movie/showtime is correct
    2. The seats are correct
    3. User has confirmed they want to book

    Args:
        showtime_id: ID of the showtime
        seat_labels: List of seat labels to book
        user_id: User making the booking

    Returns:
        Dict with booking result
    """
    from uuid import UUID

    from sqlalchemy import and_, select

    from app.models.booking import Booking, BookingStatus
    from app.models.seat import Seat, SeatStatus
    from app.shared.db.database import SessionLocal

    db = SessionLocal()
    try:
        # Find seats by labels
        seats = db.execute(
            select(Seat).where(
                and_(
                    Seat.showtime_id == showtime_id,
                    Seat.seat_label.in_(seat_labels),
                )
            )
        ).scalars().all()

        if len(seats) != len(seat_labels):
            found = [s.seat_label for s in seats]
            missing = [l for l in seat_labels if l not in found]
            return {
                "success": False,
                "message": f"Seats not found: {', '.join(missing)}",
            }

        # Check availability
        unavailable = [s.seat_label for s in seats if s.status != SeatStatus.AVAILABLE]
        if unavailable:
            return {
                "success": False,
                "message": f"Seats already booked: {', '.join(unavailable)}",
            }

        # Calculate total price (simplified - use showtime base_price * seats)
        from app.models.showtime import Showtime
        showtime = db.get(Showtime, showtime_id)
        if not showtime:
            return {"success": False, "message": "Showtime not found"}

        total_price = showtime.base_price * len(seats)

        # Create booking
        booking_code = str(uuid4())[:8].upper()
        booking = Booking(
            user_id=UUID(user_id),
            showtime_id=showtime_id,
            total_price=total_price,
            status=BookingStatus.PENDING,
            booking_code=booking_code,
        )
        db.add(booking)
        db.flush()

        # Mark seats as held
        for seat in seats:
            seat.status = SeatStatus.HELD

        db.commit()

        return {
            "success": True,
            "booking_code": booking_code,
            "total_price": total_price,
            "seats": seat_labels,
            "message": f"Booking created! Code: {booking_code}",
        }
    except Exception as e:
        db.rollback()
        return {"success": False, "message": str(e)}
    finally:
        db.close()
