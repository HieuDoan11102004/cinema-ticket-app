"""Showtime service for business logic."""
from typing import List, Optional

from sqlalchemy.orm import Session

from app.modules.showtimes.showtime_repository import ShowtimeRepository
from app.modules.showtimes.dto.showtime_dto import ShowtimeResponse


class ShowtimeService:
    """Service for showtime operations."""

    def __init__(self, db: Session):
        self.db = db
        self.repository = ShowtimeRepository(db)

    def _to_response(self, showtime) -> ShowtimeResponse:
        """Convert showtime model to response DTO."""
        return ShowtimeResponse(
            id=showtime.id,
            film_id=showtime.film_id,
            film_title=showtime.film.title if showtime.film else "",
            cinema_room=showtime.cinema_room,
            start_time=showtime.start_time,
            base_price=float(showtime.base_price),
        )

    def get_showtime_by_id(self, showtime_id: int) -> Optional[ShowtimeResponse]:
        """Get a single showtime by ID."""
        showtime = self.repository.get_by_id(showtime_id)
        if not showtime:
            return None
        return self._to_response(showtime)

    def get_showtimes_for_film(
        self,
        film_id: int,
        skip: int = 0,
        limit: int = 100,
        upcoming_only: bool = True,
    ) -> tuple[List[ShowtimeResponse], int]:
        """Get showtimes for a specific film."""
        showtimes, total = self.repository.get_by_film_id(
            film_id=film_id,
            skip=skip,
            limit=limit,
            upcoming_only=upcoming_only,
        )
        return [self._to_response(s) for s in showtimes], total

    def get_all_showtimes(
        self,
        skip: int = 0,
        limit: int = 100,
        upcoming_only: bool = True,
    ) -> tuple[List[ShowtimeResponse], int]:
        """Get all showtimes."""
        showtimes, total = self.repository.get_all(
            skip=skip,
            limit=limit,
            upcoming_only=upcoming_only,
        )
        return [self._to_response(s) for s in showtimes], total
