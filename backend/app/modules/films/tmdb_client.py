"""TMDB API client for fetching movie data."""
import asyncio
from datetime import date
from typing import Optional

import httpx

from app.shared.core.config import _yaml

_tmdb_config = _yaml.get("tmdb", {})


# TMDB genre IDs to names mapping
TMDB_GENRES = {
    28: "Action",
    12: "Adventure",
    16: "Animation",
    35: "Comedy",
    80: "Crime",
    99: "Documentary",
    18: "Drama",
    10751: "Family",
    14: "Fantasy",
    36: "History",
    27: "Horror",
    10402: "Music",
    9648: "Mystery",
    10749: "Romance",
    878: "Science Fiction",
    10770: "TV Movie",
    53: "Thriller",
    10752: "War",
    37: "Western",
}


class TMDBClient:
    """Client for The Movie Database (TMDB) API."""

    def __init__(self) -> None:
        self.api_key = _tmdb_config.get("api_key", "")
        self.access_token = _tmdb_config.get("access_token", "")
        self.base_url = _tmdb_config.get("base_url", "https://api.themoviedb.org/3")
        self.image_base_url = _tmdb_config.get("image_base_url", "https://image.tmdb.org/t/p")
        self.poster_sizes = _tmdb_config.get("poster_sizes", ["w500", "original"])

    def _get_headers(self) -> dict:
        """Get HTTP headers with authentication."""
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }

    def _get_poster_url(self, poster_path: Optional[str], size: str = "w500") -> Optional[str]:
        """Build full poster URL from TMDB path."""
        if not poster_path:
            return None
        return f"{self.image_base_url}/{size}{poster_path}"

    async def get_popular_movies(self, page: int = 1, language: str = "en-US") -> dict:
        """Fetch popular movies from TMDB."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/movie/popular",
                headers=self._get_headers(),
                params={"api_key": self.api_key, "page": page, "language": language},
                timeout=30.0,
            )
            response.raise_for_status()
            return response.json()

    async def get_movie_details(self, movie_id: int, language: str = "en-US") -> dict:
        """Fetch detailed info for a single movie."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/movie/{movie_id}",
                headers=self._get_headers(),
                params={"api_key": self.api_key, "language": language},
                timeout=30.0,
            )
            response.raise_for_status()
            return response.json()

    async def get_now_playing(self, page: int = 1, language: str = "en-US") -> dict:
        """Fetch movies currently in theaters."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/movie/now_playing",
                headers=self._get_headers(),
                params={"api_key": self.api_key, "page": page, "language": language},
                timeout=30.0,
            )
            response.raise_for_status()
            return response.json()

    async def get_upcoming(self, page: int = 1, language: str = "en-US") -> dict:
        """Fetch upcoming movies."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/movie/upcoming",
                headers=self._get_headers(),
                params={"api_key": self.api_key, "page": page, "language": language},
                timeout=30.0,
            )
            response.raise_for_status()
            return response.json()

    async def search_movies(self, query: str, page: int = 1, language: str = "en-US") -> dict:
        """Search for movies by title."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/search/movie",
                headers=self._get_headers(),
                params={
                    "api_key": self.api_key,
                    "query": query,
                    "page": page,
                    "language": language,
                },
                timeout=30.0,
            )
            response.raise_for_status()
            return response.json()

    def parse_tmdb_movie(self, data: dict) -> dict:
        """Transform TMDB movie data to our Film model schema."""
        # Parse release date (YYYY-MM-DD string -> date object)
        release_date = None
        if data.get("release_date"):
            try:
                parts = data["release_date"].split("-")
                release_date = date(int(parts[0]), int(parts[1]), int(parts[2]))
            except (ValueError, IndexError):
                pass

        # Resolve genre IDs to names
        genre_ids = data.get("genre_ids", [])
        if not genre_ids and data.get("genres"):
            # If full genre objects are provided, use name field
            genre_ids = [g["id"] for g in data.get("genres", [])]

        genres = [TMDB_GENRES.get(gid, str(gid)) for gid in genre_ids]

        return {
            "title": data.get("title", ""),
            "genres": genres,
            "overview": data.get("overview"),
            "poster_url": self._get_poster_url(data.get("poster_path"), "w500"),
            "duration_min": data.get("runtime"),
            "release_date": release_date,
            "tmdb_id": data.get("id"),
        }


# Singleton instance
tmdb_client = TMDBClient()
