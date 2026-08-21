"""Background worker for handling expired seat locks.

This worker periodically checks for orphaned holds and releases them.
It can be run as a separate process or integrated with the main app.
"""
import asyncio
import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.seat import Seat, SeatStatus
from app.shared.redis import redis_client

logger = logging.getLogger(__name__)


class SeatLockWorker:
    """Background worker to clean up expired seat holds."""

    SEAT_LOCK_PREFIX = "seat_lock"
    POLL_INTERVAL = 30  # seconds

    def __init__(self, db_session_factory):
        """
        Initialize the worker.

        Args:
            db_session_factory: SQLAlchemy sessionmaker or similar factory
        """
        self.db_factory = db_session_factory

    async def _release_expired_holds(self) -> int:
        """
        Find and release seats that are marked as HELD in Postgres
        but have no corresponding Redis lock (TTL expired).

        Returns:
            Number of seats released
        """
        released = 0

        async with self.db_factory() as db:
            # Find all HELD seats
            stmt = select(Seat).where(Seat.status == SeatStatus.HELD)
            held_seats = list(db.scalars(stmt).all())

            if not held_seats:
                return 0

            # Group by showtime for efficient key lookup
            by_showtime: dict[int, list[int]] = {}
            seat_map: dict[int, Seat] = {}
            for seat in held_seats:
                if seat.showtime_id not in by_showtime:
                    by_showtime[seat.showtime_id] = []
                by_showtime[seat.showtime_id].append(seat.id)
                seat_map[seat.id] = seat

            redis_client_instance = redis_client.client

            # Check each showtime's seats
            for showtime_id, seat_ids in by_showtime.items():
                keys = [
                    f"{self.SEAT_LOCK_PREFIX}:{showtime_id}:{sid}"
                    for sid in seat_ids
                ]

                # Batch check Redis keys
                redis_values = await redis_client_instance.mget(keys)

                # Find seats with no Redis lock
                seats_to_release = []
                for i, seat_id in enumerate(seat_ids):
                    if redis_values[i] is None:
                        seats_to_release.append(seat_id)

                # Release seats with no lock
                if seats_to_release:
                    stmt = (
                        select(Seat)
                        .where(Seat.id.in_(seats_to_release))
                        .with_for_update()
                    )
                    seats = list(db.scalars(stmt).all())

                    for seat in seats:
                        seat.status = SeatStatus.AVAILABLE

                    db.commit()
                    released += len(seats_to_release)
                    logger.info(
                        f"Released {len(seats_to_release)} expired seat holds "
                        f"for showtime {showtime_id}: {seats_to_release}"
                    )

        return released

    async def _release_user_holds(self, user_id: str) -> int:
        """
        Release all holds for a specific user (e.g., booking cancelled).

        Returns:
            Number of holds released
        """
        from app.modules.seats.seat_lock_service import SeatLockService

        user_key = f"user_holds:{user_id}"
        holds = await redis_client.client.smembers(user_key)

        if not holds:
            return 0

        # Parse hold keys (format: showtime_id:seat_id)
        by_showtime: dict[int, list[int]] = {}
        for hold_key in holds:
            parts = hold_key.split(":")
            if len(parts) == 2:
                try:
                    showtime_id = int(parts[0])
                    seat_id = int(parts[1])
                    if showtime_id not in by_showtime:
                        by_showtime[showtime_id] = []
                    by_showtime[showtime_id].append(seat_id)
                except ValueError:
                    continue

        released = 0
        for showtime_id, seat_ids in by_showtime.items():
            keys = [
                f"{self.SEAT_LOCK_PREFIX}:{showtime_id}:{sid}"
                for sid in seat_ids
            ]
            await redis_client.client.delete(*keys)
            released += len(seat_ids)

        await redis_client.client.delete(user_key)
        return released

    async def run(self) -> None:
        """
        Run the worker loop.

        This will periodically check for expired holds and release them.
        """
        logger.info("Starting seat lock worker...")

        while True:
            try:
                released = await self._release_expired_holds()
                if released > 0:
                    logger.info(f"Seat lock worker: released {released} expired holds")

                await asyncio.sleep(self.POLL_INTERVAL)

            except asyncio.CancelledError:
                logger.info("Seat lock worker shutting down...")
                break
            except Exception as e:
                logger.error(f"Seat lock worker error: {e}")
                await asyncio.sleep(5)  # Back off on error

    async def cleanup_once(self) -> int:
        """
        Run cleanup once (useful for testing or manual cleanup).

        Returns:
            Number of seats released
        """
        return await self._release_expired_holds()
