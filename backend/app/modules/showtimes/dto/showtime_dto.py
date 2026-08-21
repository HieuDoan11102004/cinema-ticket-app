"""Showtime DTOs."""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict


class ShowtimeResponse(BaseModel):
    """Showtime response schema."""
    id: int
    film_id: int
    film_title: str
    cinema_room: str
    start_time: datetime
    base_price: float

    model_config = ConfigDict(from_attributes=True)


class ShowtimeListResponse(BaseModel):
    """Paginated showtime list response."""
    showtimes: List[ShowtimeResponse]
    total: int
