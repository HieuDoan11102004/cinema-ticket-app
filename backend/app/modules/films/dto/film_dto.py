"""Film DTOs for API responses."""
from datetime import date
from typing import Optional, List

from pydantic import BaseModel


class FilmResponse(BaseModel):
    """Film response schema."""

    id: int
    title: str
    genres: List[str] = []
    overview: Optional[str] = None
    poster_url: Optional[str] = None
    duration_min: Optional[int] = None
    release_date: Optional[date] = None
    tmdb_id: Optional[int] = None

    class Config:
        from_attributes = True


class FilmListResponse(BaseModel):
    """Paginated film list response."""

    films: List[FilmResponse]
    total: int
    page: int
    per_page: int


class FilmSyncResponse(BaseModel):
    """Film sync result response."""

    popular: dict
    now_playing: dict
    upcoming: dict
    total_films: int
