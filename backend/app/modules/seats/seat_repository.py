"""Seat repository for database operations."""
from typing import List
from sqlalchemy import select, and_
from sqlalchemy.orm import Session

from app.models.seat import Seat, SeatStatus


class SeatRepository:
    """Repository for Seat database operations."""

    def __init__(self, db: Session):
        self.db = db

    def get_by_showtime_id(self, showtime_id: int) -> List[Seat]:
        """Get all seats for a showtime."""
        stmt = select(Seat).where(Seat.showtime_id == showtime_id)
        return list(self.db.scalars(stmt).all())

    def get_by_ids(self, seat_ids: List[int]) -> List[Seat]:
        """Get seats by their IDs."""
        stmt = select(Seat).where(Seat.id.in_(seat_ids))
        return list(self.db.scalars(stmt).all())

    def get_available_seats(self, seat_ids: List[int]) -> List[Seat]:
        """Get seats that are currently available from a list of IDs."""
        stmt = select(Seat).where(
            and_(
                Seat.id.in_(seat_ids),
                Seat.status == SeatStatus.AVAILABLE
            )
        )
        return list(self.db.scalars(stmt).all())

    def update_status(self, seat_ids: List[int], status: SeatStatus) -> List[Seat]:
        """Update status for multiple seats."""
        self.db.query(Seat).filter(Seat.id.in_(seat_ids)).update(
            {"status": status},
            synchronize_session=False
        )
        self.db.commit()
        return self.get_by_ids(seat_ids)
