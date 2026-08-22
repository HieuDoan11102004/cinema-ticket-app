"""Get showtimes tool."""
from datetime import datetime
from typing import Annotated

from langchain_core.tools import tool


@tool
def get_showtimes(
    film_id: Annotated[int | None, "Film ID to get showtimes for (optional if query provided)"] = None,
    query: Annotated[str | None, "Movie title to search for"] = None,
    date: Annotated[str | None, "Date in YYYY-MM-DD format"] = None,
    limit: Annotated[int, "Maximum number of showtimes"] = 10,
) -> dict:
    """
    Get available showtimes for a movie.

    Use this when the user asks about when a movie is playing,
    or wants to see available times.

    Args:
        film_id: Specific film ID (preferred if known)
        query: Movie title to search for (used if film_id not provided)
        date: Filter by date (YYYY-MM-DD format)
        limit: Maximum results

    Returns:
        Dict with showtimes list
    """
    from app.modules.films.film_repository import FilmRepository
    from sqlalchemy import and_, select
    from app.shared.db.database import SessionLocal
    from app.models.showtime import Showtime

    db = SessionLocal()
    try:
        # Get film_id from query if not provided
        if film_id is None and query:
            repo = FilmRepository(db)
            films, _ = repo.search_fts(query=query, status="Released", skip=0, limit=1)
            if films:
                film_id = films[0].id

        if film_id is None:
            return {"showtimes": [], "message": "No film specified"}

        # Build query
        stmt = select(Showtime).where(Showtime.film_id == film_id)

        if date:
            try:
                target_date = datetime.strptime(date, "%Y-%m-%d").date()
                from datetime import timedelta
                stmt = stmt.where(
                    and_(
                        Showtime.start_time >= datetime.combine(target_date, datetime.min.time()),
                        Showtime.start_time < datetime.combine(target_date, datetime.max.time()),
                    )
                )
            except ValueError:
                pass  # Invalid date format, ignore filter

        stmt = stmt.order_by(Showtime.start_time).limit(limit)
        result = db.execute(stmt)
        showtimes = result.scalars().all()

        return {
            "showtimes": [
                {
                    "id": s.id,
                    "start_time": s.start_time.isoformat(),
                    "cinema_room": s.cinema_room,
                    "base_price": s.base_price,
                }
                for s in showtimes
            ],
            "count": len(showtimes),
        }
    finally:
        db.close()
