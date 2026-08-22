"""Search movies tool."""
from typing import Annotated, Sequence

from langchain_core.messages import BaseMessage
from langchain_core.tools import tool
from sqlalchemy.orm import Session

from app.modules.films.film_repository import FilmRepository


@tool
def search_movies(
    query: Annotated[str, "Movie title or keywords to search for"],
    genres: Annotated[list[str] | None, "List of genres to filter by"] = None,
    limit: Annotated[int, "Maximum number of results"] = 10,
) -> dict:
    """
    Search for movies by title, genre, or keywords.

    Use this when the user wants to find information about movies,
    see what's playing, or get movie recommendations.

    Args:
        query: Search query (movie title, actor, director, etc.)
        genres: Optional list of genres to filter by
        limit: Maximum number of results (default 10)

    Returns:
        Dict with list of matching movies
    """
    from app.shared.db.database import SessionLocal

    db: Session = SessionLocal()
    try:
        repository = FilmRepository(db)
        films, _ = repository.search_fts(
            query=query,
            genres=genres,
            status="Released",
            skip=0,
            limit=limit,
        )

        return {
            "movies": [
                {
                    "id": film.id,
                    "title": film.title,
                    "tagline": film.tagline,
                    "genres": film.genres,
                    "overview": film.overview,
                    "vote_average": film.vote_average,
                    "runtime": film.runtime,
                    "poster_url": film.poster_url,
                }
                for film in films
            ],
            "count": len(films),
        }
    finally:
        db.close()
