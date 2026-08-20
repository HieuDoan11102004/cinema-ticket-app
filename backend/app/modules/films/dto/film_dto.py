"""Film DTOs for API responses."""
from datetime import date
from typing import Optional, List

from pydantic import BaseModel


class FilmResponse(BaseModel):
    """Film response schema."""

    id: int
    title: str
    original_title: Optional[str] = None
    tagline: Optional[str] = None
    overview: Optional[str] = None
    release_date: Optional[date] = None
    poster_url: Optional[str] = None
    backdrop_url: Optional[str] = None
    trailer_url: Optional[str] = None
    genres: List[str] = []
    original_language: str = "en"
    spoken_languages: List[str] = []
    production_countries: List[str] = []
    production_companies: List[str] = []
    runtime: Optional[int] = None
    status: Optional[str] = None
    adult: bool = False
    tmdb_id: Optional[int] = None
    imdb_id: Optional[str] = None
    homepage: Optional[str] = None
    budget: int = 0
    revenue: int = 0
    vote_average: float = 0.0
    vote_count: int = 0
    popularity: float = 0.0

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
