"""Film service for syncing and managing films from TMDB."""
import asyncio
from typing import List, Optional, Tuple

from sqlalchemy.orm import Session

from app.modules.films.film_repository import FilmRepository
from app.modules.films.tmdb_client import tmdb_client


class FilmService:
    """Service for syncing films from TMDB and managing film data."""

    def __init__(self, db: Session):
        self.repository = FilmRepository(db)
        self.client = tmdb_client

    async def sync_popular_movies(self, pages: int = 5) -> Tuple[int, int]:
        """
        Sync popular movies from TMDB.
        Returns (created_count, updated_count).
        """
        created, updated = 0, 0

        for page in range(1, pages + 1):
            data = await self.client.get_popular_movies(page=page)
            movies = data.get("results", [])

            for movie_data in movies:
                film_data = self.client.parse_tmdb_movie(movie_data)
                film, was_created = self.repository.upsert(
                    tmdb_id=film_data["tmdb_id"],
                    film_data=film_data,
                )
                if was_created:
                    created += 1
                else:
                    updated += 1

        return created, updated

    async def sync_now_playing(self, pages: int = 3) -> Tuple[int, int]:
        """Sync movies currently in theaters."""
        created, updated = 0, 0

        for page in range(1, pages + 1):
            data = await self.client.get_now_playing(page=page)
            movies = data.get("results", [])

            for movie_data in movies:
                film_data = self.client.parse_tmdb_movie(movie_data)
                film, was_created = self.repository.upsert(
                    tmdb_id=film_data["tmdb_id"],
                    film_data=film_data,
                )
                if was_created:
                    created += 1
                else:
                    updated += 1

        return created, updated

    async def sync_upcoming(self, pages: int = 3) -> Tuple[int, int]:
        """Sync upcoming movies."""
        created, updated = 0, 0

        for page in range(1, pages + 1):
            data = await self.client.get_upcoming(page=page)
            movies = data.get("results", [])

            for movie_data in movies:
                film_data = self.client.parse_tmdb_movie(movie_data)
                film, was_created = self.repository.upsert(
                    tmdb_id=film_data["tmdb_id"],
                    film_data=film_data,
                )
                if was_created:
                    created += 1
                else:
                    updated += 1

        return created, updated

    async def sync_all(self) -> dict:
        """Sync all categories of movies."""
        results = {
            "popular": {"created": 0, "updated": 0},
            "now_playing": {"created": 0, "updated": 0},
            "upcoming": {"created": 0, "updated": 0},
        }

        # Run all syncs concurrently
        popular_task = self.sync_popular_movies(pages=5)
        now_playing_task = self.sync_now_playing(pages=3)
        upcoming_task = self.sync_upcoming(pages=3)

        popular_results, now_playing_results, upcoming_results = await asyncio.gather(
            popular_task, now_playing_task, upcoming_task
        )

        results["popular"]["created"], results["popular"]["updated"] = popular_results
        results["now_playing"]["created"], results["now_playing"]["updated"] = now_playing_results
        results["upcoming"]["created"], results["upcoming"]["updated"] = upcoming_results

        results["total_films"] = self.repository.count() # type: ignore[arg-type]

        return results

    async def get_movie_details_from_tmdb(self, tmdb_id: int) -> dict:
        """Fetch detailed movie info from TMDB (including runtime, genres)."""
        data = await self.client.get_movie_details(tmdb_id)
        return self.client.parse_tmdb_movie(data)

    async def enrich_film_details(self, film_id: int) -> Optional[dict]:
        """Fetch full details from TMDB and update local film."""
        film = self.repository.get_by_id(film_id)
        if not film or not film.tmdb_id:# type: ignore[arg-type]

            return None

        film_data = await self.get_movie_details_from_tmdb(film.tmdb_id)# type: ignore[arg-type]

        updated_film = self.repository.update(film, film_data)
        return updated_film

    def get_films(self, skip: int = 0, limit: int = 100) -> List:
        """Get local films."""
        return self.repository.get_all(skip=skip, limit=limit)

    def get_film_by_id(self, film_id: int):
        """Get single film by ID."""
        return self.repository.get_by_id(film_id)

    def get_film_by_tmdb_id(self, tmdb_id: int):
        """Get film by TMDB ID."""
        return self.repository.get_by_tmdb_id(tmdb_id)

    def search_films(
        self,
        query: Optional[str] = None,
        genres: Optional[List[str]] = None,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 20,
    ) -> Tuple[List, int]:
        """Search films with filters (legacy ILIKE search)."""
        return self.repository.search(
            query=query,
            genres=genres,
            status=status,
            skip=skip,
            limit=limit,
        )

    def search_films_fts(
        self,
        query: Optional[str] = None,
        genres: Optional[List[str]] = None,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 20,
    ) -> Tuple[List, int]:
        """
        Search films using PostgreSQL full-text search.

        Features:
        - Fast GIN index-based search
        - Weighted ranking (title > overview > genres)
        - Better relevance scoring

        Falls back to ILIKE search if FTS columns don't exist.
        """
        try:
            return self.repository.search_fts(
                query=query,
                genres=genres,
                status=status,
                skip=skip,
                limit=limit,
            )
        except Exception:
            # Fallback to ILIKE search
            return self.repository.search(
                query=query,
                genres=genres,
                status=status,
                skip=skip,
                limit=limit,
            )
