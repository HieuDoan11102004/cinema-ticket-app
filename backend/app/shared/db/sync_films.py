"""CLI script to sync films from TMDB to database."""
import asyncio
import sys
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parents[2]))

from app.shared.db.database import SessionLocal
from app.modules.films.film_service import FilmService


async def main():
    """Sync films from TMDB."""
    db = SessionLocal()
    try:
        service = FilmService(db)

        print("🔄 Syncing films from TMDB...")
        print("=" * 50)

        results = await service.sync_all()

        print("\n📊 Sync Results:")
        print(f"  Popular movies: {results['popular']['created']} created, {results['popular']['updated']} updated")
        print(f"  Now playing: {results['now_playing']['created']} created, {results['now_playing']['updated']} updated")
        print(f"  Upcoming: {results['upcoming']['created']} created, {results['upcoming']['updated']} updated")
        print(f"\n📁 Total films in database: {results['total_films']}")

        total_created = (
            results["popular"]["created"]
            + results["now_playing"]["created"]
            + results["upcoming"]["created"]
        )
        print(f"\n✅ Done! {total_created} new films added.")

    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(main())
