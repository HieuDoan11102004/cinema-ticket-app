"""Seat service for business logic with Redis-based distributed locking."""
from typing import List, Optional
from uuid import UUID

import redis.asyncio as redis
from sqlalchemy.orm import Session

from app.modules.seats.seat_repository import SeatRepository
from app.modules.seats.seat_lock_service import SeatLockService
from app.modules.seats.dto.seat_dto import (
    SeatResponse,
    SeatListResponse,
    SeatActionResponse,
    HoldExpiryResponse,
)
from app.models.seat import SeatStatus
from app.shared.core.config import SEAT_HOLD_TTL


class SeatService:
    """Service for seat operations with Redis distributed locking."""

    def __init__(self, db: Session, redis_client: Optional[redis.Redis] = None):
        self.db = db
        self.repository = SeatRepository(db)
        self._redis_client = redis_client
        self._lock_service: Optional[SeatLockService] = None

    @property
    def lock_service(self) -> SeatLockService:
        """Lazy initialization of lock service."""
        if self._lock_service is None:
            if self._redis_client is None:
                raise RuntimeError("Redis client not provided")
            self._lock_service = SeatLockService(self._redis_client)
        return self._lock_service

    def _to_response(self, seat) -> SeatResponse:
        """Convert seat model to response DTO."""
        return SeatResponse(
            id=seat.id,
            showtime_id=seat.showtime_id,
            seat_label=seat.seat_label,
            status=seat.status,
        )

    def get_seats_for_showtime(self, showtime_id: int) -> SeatListResponse:
        """Get all seats for a showtime with their statuses."""
        seats = self.repository.get_by_showtime_id(showtime_id)
        return SeatListResponse(
            seats=[self._to_response(s) for s in seats],
            total=len(seats),
        )

    async def hold_seats(
        self,
        seat_ids: List[int],
        showtime_id: int,
        user_id: UUID,
        ttl: int = SEAT_HOLD_TTL,
    ) -> SeatActionResponse:
        """
        Attempt to hold seats temporarily using Redis distributed locks.

        This implements a hybrid locking strategy:
        1. Fast rejection from Postgres (seats already booked)
        2. Atomic Redis lock acquisition
        3. Postgres status update (for durability)
        """
        # Step 1: Validate seats exist and belong to this showtime
        seats = self.repository.get_by_ids(seat_ids)
        if len(seats) != len(seat_ids):
            return SeatActionResponse(
                success=False,
                message="One or more seats not found",
                released_seats=[],
            )

        for seat in seats:
            if seat.showtime_id != showtime_id:  # type: ignore[arg-type]
                return SeatActionResponse(
                    success=False,
                    message=f"Seat {seat.seat_label} does not belong to this showtime",
                    released_seats=[],
                )

        # Step 2: Fast rejection for already BOOKED seats (not just HELD)
        booked_seats = [
            s for s in seats if s.status == SeatStatus.BOOKED
        ]
        if booked_seats:
            return SeatActionResponse(
                success=False,
                message=f"Seats {[s.seat_label for s in booked_seats]} are already booked",
                released_seats=[],
            )

        # Step 3: Try to acquire Redis locks atomically
        success, failed_seat_ids = await self.lock_service.acquire_locks(
            seat_ids=seat_ids,
            showtime_id=showtime_id,
            user_id=user_id,
            ttl=ttl,
        )

        if not success:
            # Some seats are locked by other users
            failed_labels = [
                s.seat_label for s in seats if s.id in failed_seat_ids
            ]
            return SeatActionResponse(
                success=False,
                message=f"Seats {failed_labels} are currently held by another user. Please try again.",
                released_seats=[],
            )

        # Step 4: Update Postgres (make HELD)
        # This is our durable record - Redis is the fast-path
        try:
            # Get available seats that are not HELD
            available_seat_ids = [
                s.id for s in seats if s.status == SeatStatus.AVAILABLE
            ]
            if available_seat_ids:
                held_seats = self.repository.update_status(
                    available_seat_ids,
                    SeatStatus.HELD
                )
            else:
                held_seats = []

            return SeatActionResponse(
                success=True,
                message=f"Successfully held {len(seat_ids)} seat(s). Complete booking within {ttl // 60} minutes.",
                released_seats=[self._to_response(s) for s in held_seats],
            )
        except Exception as e:
            # Rollback Redis locks if Postgres update fails
            await self.lock_service.release_locks(
                seat_ids=seat_ids,
                showtime_id=showtime_id,
                user_id=user_id,
            )
            return SeatActionResponse(
                success=False,
                message=f"Failed to hold seats: {str(e)}",
                released_seats=[],
            )

    async def release_seats(
        self,
        seat_ids: List[int],
        showtime_id: int,
        user_id: UUID,
    ) -> SeatActionResponse:
        """
        Release held seats back to available status.

        Verifies user owns the Redis locks before releasing.
        """
        # Validate seats exist
        seats = self.repository.get_by_ids(seat_ids)
        if len(seats) != len(seat_ids):
            return SeatActionResponse(
                success=False,
                message="One or more seats not found",
                released_seats=[],
            )

        # Verify seats belong to showtime
        for seat in seats:
            if seat.showtime_id != showtime_id:  # type: ignore[arg-type]
                return SeatActionResponse(
                    success=False,
                    message=f"Seat {seat.seat_label} does not belong to this showtime",
                    released_seats=[],
                )

        # Release Redis locks (only if owned by user)
        released_count, not_owned = await self.lock_service.release_locks(
            seat_ids=seat_ids,
            showtime_id=showtime_id,
            user_id=user_id,
        )

        # Update Postgres regardless of Redis result
        # (user might have Redis lock expired but Postgres still shows HELD)
        released_seats = self.repository.update_status(
            seat_ids,
            SeatStatus.AVAILABLE
        )

        if not_owned > 0:
            return SeatActionResponse(
                success=True,
                message=f"Released {released_count} seat(s) ({not_owned} not owned by you)",
                released_seats=[self._to_response(s) for s in released_seats],
            )

        return SeatActionResponse(
            success=True,
            message=f"Successfully released {len(seat_ids)} seat(s)",
            released_seats=[self._to_response(s) for s in released_seats],
        )

    async def extend_hold(
        self,
        seat_ids: List[int],
        showtime_id: int,
        user_id: UUID,
        extra_seconds: int = 300,
    ) -> HoldExpiryResponse:
        """
        Extend the hold duration for seats.

        Args:
            extra_seconds: Additional seconds to add (default 5 minutes)
        """
        # Extend Redis locks
        extended, not_owned = await self.lock_service.extend_locks(
            seat_ids=seat_ids,
            showtime_id=showtime_id,
            user_id=user_id,
            extra_seconds=extra_seconds,
        )

        if not_owned > 0:
            # Get remaining TTL for owned seats
            remaining = await self.lock_service.get_remaining_ttl(
                seat_ids=seat_ids,
                showtime_id=showtime_id,
                user_id=user_id,
            )
            avg_remaining = (
                sum(remaining.values()) // len(remaining)
                if remaining else 0
            )
            return HoldExpiryResponse(
                success=False,
                message=f"Could not extend {not_owned} seat(s) - not owned by you",
                extended_count=extended,
                remaining_seconds=avg_remaining,
            )

        # Get new TTL
        remaining = await self.lock_service.get_remaining_ttl(
            seat_ids=seat_ids,
            showtime_id=showtime_id,
            user_id=user_id,
        )
        avg_remaining = (
            sum(remaining.values()) // len(remaining)
            if remaining else 0
        )

        return HoldExpiryResponse(
            success=True,
            message=f"Extended {extended} seat(s) by {extra_seconds} seconds",
            extended_count=extended,
            remaining_seconds=avg_remaining,
        )

    async def check_hold_status(
        self,
        seat_ids: List[int],
        showtime_id: int,
        user_id: UUID,
    ) -> dict:
        """
        Check hold status for seats.

        Returns info about which seats are held and by whom.
        """
        # Get Redis lock status
        lock_holders = await self.lock_service.check_locks(
            seat_ids=seat_ids,
            showtime_id=showtime_id,
        )

        # Get remaining TTL for user's holds
        remaining_ttl = await self.lock_service.get_remaining_ttl(
            seat_ids=seat_ids,
            showtime_id=showtime_id,
            user_id=user_id,
        )

        return {
            "seats": {
                seat_id: {
                    "locked_by_current_user": lock_holders.get(seat_id) == str(user_id),
                    "locked_by": lock_holders.get(seat_id),
                    "remaining_ttl": remaining_ttl.get(seat_id, 0),
                }
                for seat_id in seat_ids
            }
        }
