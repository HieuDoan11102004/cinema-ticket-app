"""Film repository for database operations."""
from typing import List, Optional

from sqlalchemy import select, func, or_, and_
from sqlalchemy.orm import Session

from app.models.film import Film


class FilmRepository:
    """Repository for Film database operations."""

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, film_id: int) -> Optional[Film]:
        """Get film by ID."""
        return self.db.get(Film, film_id)

    def get_by_tmdb_id(self, tmdb_id: int) -> Optional[Film]:
        """Get film by TMDB ID."""
        stmt = select(Film).where(Film.tmdb_id == tmdb_id)
        return self.db.scalar(stmt)

    def get_all(self, skip: int = 0, limit: int = 100) -> List[Film]:
        """Get all films with pagination."""
        stmt = select(Film).offset(skip).limit(limit)
        return list(self.db.scalars(stmt).all())

    def create(self, film_data: dict) -> Film:
        """Create a new film."""
        film = Film(**film_data)
        self.db.add(film)
        self.db.commit()
        self.db.refresh(film)
        return film

    def update(self, film: Film, film_data: dict) -> Film:
        """Update an existing film."""
        for key, value in film_data.items():
            if hasattr(film, key) and value is not None:
                setattr(film, key, value)
        self.db.commit()
        self.db.refresh(film)
        return film

    def upsert(self, tmdb_id: int, film_data: dict) -> tuple[Film, bool]:
        """
        Insert or update a film based on TMDB ID.
        Returns (film, created) tuple.
        """
        existing = self.get_by_tmdb_id(tmdb_id)
        if existing:
            return self.update(existing, film_data), False
        return self.create(film_data), True

    def delete(self, film_id: int) -> bool:
        """Delete a film by ID."""
        film = self.get_by_id(film_id)
        if film:
            self.db.delete(film)
            self.db.commit()
            return True
        return False

    def count(self) -> int:
        """Count total films."""
        stmt = select(func.count(Film.id))
        return self.db.scalar(stmt) or 0

    def _build_genre_condition(self, genres: List[str]):
        """Build SQL condition for genre filtering using PostgreSQL ANY()."""
        if not genres:
            return None
        # Use OR to match any of the selected genres
        return or_(*[Film.genres.any(g) for g in genres])

    def search(
        self,
        query: Optional[str] = None,
        genres: Optional[List[str]] = None,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[List[Film], int]:
        """
        Search films with optional filters.
        Returns (films, total_count) tuple.
        """
        stmt = select(Film)
        conditions = []

        if query:
            conditions.append(Film.title.ilike(f"%{query}%"))

        if status:
            conditions.append(Film.status == status)

        if genres:
            conditions.append(self._build_genre_condition(genres))

        if conditions:
            stmt = stmt.where(and_(*conditions))

        # Get total count
        count_stmt = select(func.count(Film.id))
        if conditions:
            count_stmt = count_stmt.where(and_(*conditions))
        total = self.db.scalar(count_stmt) or 0

        # Apply pagination
        stmt = stmt.offset(skip).limit(limit)
        films = list(self.db.scalars(stmt).all())

        return films, total
