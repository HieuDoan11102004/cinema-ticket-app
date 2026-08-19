"""Films module - TMDB integration for movie data."""
from app.modules.films.tmdb_client import tmdb_client
from app.modules.films.film_repository import FilmRepository
from app.modules.films.film_service import FilmService

__all__ = ["tmdb_client", "FilmRepository", "FilmService"]
