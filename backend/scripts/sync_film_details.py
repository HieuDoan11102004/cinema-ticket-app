"""Sync film details from TMDB for all existing films.

This script fetches full movie details (including runtime, tagline, budget, etc.)
from TMDB for all films currently in the database.
"""
import asyncio
import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy.orm import Session
from app.shared.db.database import SessionLocal
from app.modules.films.film_repository import FilmRepository
from app.modules.films.tmdb_client import tmdb_client


async def sync_film_details(film_ids: list[int] | None = None, batch_size: int = 10) -> dict:
    """Sync detailed info for films from TMDB."""
    db: Session = SessionLocal()
    repository = FilmRepository(db)

    # Get all films or specific ones
    if film_ids:
        films = [repository.get_by_id(fid) for fid in film_ids]
        films = [f for f in films if f and f.tmdb_id] # type: ignore[arg-type]
    else:
        films = repository.get_all(skip=0, limit=10000)
        films = [f for f in films if f.tmdb_id] # type: ignore[arg-type]

    total = len(films)
    updated = 0
    errors = 0

    print(f"Found {total} films to sync")

    for i in range(0, total, batch_size):
        batch = films[i:i + batch_size]
        tasks = []

        for film in batch:
            if film and film.tmdb_id: # type: ignore[arg-type]
                tasks.append((film, film.tmdb_id))

        # Process batch concurrently
        for film, tmdb_id in tasks:
            try:
                # Fetch full details from TMDB
                data = await tmdb_client.get_movie_details(tmdb_id)
                film_data = tmdb_client.parse_tmdb_movie(data)

                # Update film in database
                repository.update(film, film_data)
                updated += 1

                print(f"[{updated}/{total}] Updated: {film.title}")

            except Exception as e:
                errors += 1
                print(f"Error updating film {film.tmdb_id}: {e}")

    db.close()

    return {
        "total": total,
        "updated": updated,
        "errors": errors,
    }


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Sync film details from TMDB")
    parser.add_argument(
        "--film-ids",
        nargs="+",
        type=int,
        help="Specific film IDs to sync (optional)",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=10,
        help="Batch size for concurrent requests (default: 10)",
    )
    args = parser.parse_args()

    print("Starting film details sync from TMDB...")
    print("-" * 50)

    result = asyncio.run(sync_film_details(
        film_ids=args.film_ids,
        batch_size=args.batch_size,
    ))

    print("-" * 50)
    print(f"Sync complete!")
    print(f"  Total films: {result['total']}")
    print(f"  Updated: {result['updated']}")
    print(f"  Errors: {result['errors']}")


if __name__ == "__main__":
    main()
