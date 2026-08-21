"""Showtime repository for database operations."""
from datetime import datetime
from typing import List, Optional

from sqlalchemy import select, and_
from sqlalchemy.orm import Session, joinedload

from app.models.showtime import Showtime


class ShowtimeRepository:
    """Repository for Showtime database operations."""

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, showtime_id: int) -> Optional[Showtime]:
        """Get showtime by ID."""
        stmt = (
            select(Showtime)
            .options(joinedload(Showtime.film))
            .where(Showtime.id == showtime_id)
        )
        return self.db.scalars(stmt).first()

    def get_by_film_id(
        self,
        film_id: int,
        skip: int = 0,
        limit: int = 100,
        upcoming_only: bool = True,
    ) -> tuple[List[Showtime], int]:
        """
        Get showtimes for a specific film.
        Returns (showtimes, total_count) tuple.
        """
        conditions = [Showtime.film_id == film_id]

        if upcoming_only:
            conditions.append(Showtime.start_time >= datetime.now())

        stmt = (
            select(Showtime)
            .options(joinedload(Showtime.film))
            .where(and_(*conditions))
            .order_by(Showtime.start_time)
        )

        # Get total count
        count_stmt = select(Showtime.id).where(and_(*conditions))
        total = len(self.db.scalars(count_stmt).all())

        # Apply pagination
        stmt = stmt.offset(skip).limit(limit)
        showtimes = list(self.db.scalars(stmt).all())

        return showtimes, total

    def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        upcoming_only: bool = True,
    ) -> tuple[List[Showtime], int]:
        """
        Get all showtimes.
        Returns (showtimes, total_count) tuple.
        """
        conditions = []

        if upcoming_only:
            conditions.append(Showtime.start_time >= datetime.now())

        stmt = (
            select(Showtime)
            .options(joinedload(Showtime.film))
            .where(and_(*conditions) if conditions else True)# type: ignore[arg-type]

            .order_by(Showtime.start_time)
        )

        # Get total count
        count_stmt = select(Showtime.id).where(and_(*conditions)) if conditions else select(Showtime.id)
        total = len(self.db.scalars(count_stmt).all())

        # Apply pagination
        stmt = stmt.offset(skip).limit(limit)
        showtimes = list(self.db.scalars(stmt).all())

        return showtimes, total
