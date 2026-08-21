"""Redis-based seat lock service for distributed locking.

This service provides atomic seat holding using Redis with TTL-based expiry.
It uses Lua scripts for atomic multi-key operations to prevent race conditions.
"""
import json
import time
from typing import Optional
from uuid import UUID

import redis.asyncio as redis

from app.shared.core.config import SEAT_HOLD_TTL


class SeatLockService:
    """Service for managing distributed seat locks in Redis."""

    # Key patterns
    SEAT_LOCK_PREFIX = "seat_lock"
    USER_HOLDS_PREFIX = "user_holds"

    # Lua script for atomic lock acquisition
    # Uses comma-separated seat IDs for Redis compatibility
    ACQUIRE_LOCKS_SCRIPT = """
    local seat_ids_str = ARGV[1]
    local user_id = ARGV[2]
    local timestamp = ARGV[3]
    local ttl = tonumber(ARGV[4])
    local showtime_id = ARGV[5]

    -- Parse comma-separated seat IDs
    local seat_ids = {}
    for seat_id in string.gmatch(seat_ids_str, "[^,]+") do
        table.insert(seat_ids, tonumber(seat_id))
    end

    local failed_seats = {}

    -- Check all seats first
    for i, seat_id in ipairs(seat_ids) do
        local key = KEYS[i]
        local existing = redis.call('GET', key)
        if existing then
            local data = cjson.decode(existing)
            -- If locked by someone else, add to failed
            if data.user_id ~= user_id then
                table.insert(failed_seats, seat_id)
            end
        end
    end

    -- If any failed, return failure with failed seat IDs
    if #failed_seats > 0 then
        return cjson.encode({success = false, failed_seats = failed_seats})
    end

    -- All seats available, acquire locks atomically
    for i, seat_id in ipairs(seat_ids) do
        local key = KEYS[i]
        local value = cjson.encode({
            user_id = user_id,
            timestamp = timestamp,
            showtime_id = showtime_id
        })
        redis.call('SET', key, value, 'EX', ttl)
    end

    -- Track user's holds
    local user_key = 'user_holds:' .. user_id
    for i, seat_id in ipairs(seat_ids) do
        local hold_key = showtime_id .. ':' .. tostring(seat_id)
        redis.call('SADD', user_key, hold_key)
    end
    redis.call('EXPIRE', user_key, ttl)

    return cjson.encode({success = true, failed_seats = {}})
    """

    # Lua script for atomic lock release
    RELEASE_LOCKS_SCRIPT = """
    local seat_ids_str = ARGV[1]
    local user_id = ARGV[2]
    local showtime_id = ARGV[3]

    -- Parse comma-separated seat IDs
    local seat_ids = {}
    for seat_id in string.gmatch(seat_ids_str, "[^,]+") do
        table.insert(seat_ids, tonumber(seat_id))
    end

    local released = 0
    local not_owned = 0

    for i, seat_id in ipairs(seat_ids) do
        local key = KEYS[i]
        local existing = redis.call('GET', key)

        if existing then
            local data = cjson.decode(existing)
            if data.user_id == user_id then
                redis.call('DEL', key)
                released = released + 1
            else
                not_owned = not_owned + 1
            end
        end
    end

    -- Remove from user's holds
    local user_key = 'user_holds:' .. user_id
    for i, seat_id in ipairs(seat_ids) do
        local hold_key = showtime_id .. ':' .. tostring(seat_id)
        redis.call('SREM', user_key, hold_key)
    end

    return cjson.encode({released = released, not_owned = not_owned})
    """

    # Lua script to extend lock TTL
    EXTEND_LOCKS_SCRIPT = """
    local seat_ids_str = ARGV[1]
    local user_id = ARGV[2]
    local extra_seconds = tonumber(ARGV[3])
    local showtime_id = ARGV[4]

    -- Parse comma-separated seat IDs
    local seat_ids = {}
    for seat_id in string.gmatch(seat_ids_str, "[^,]+") do
        table.insert(seat_ids, tonumber(seat_id))
    end

    local extended = 0
    local not_owned = 0

    for i, seat_id in ipairs(seat_ids) do
        local key = KEYS[i]
        local existing = redis.call('GET', key)

        if existing then
            local data = cjson.decode(existing)
            if data.user_id == user_id then
                redis.call('EXPIRE', key, extra_seconds)
                extended = extended + 1
            else
                not_owned = not_owned + 1
            end
        end
    end

    -- Extend user's holds set
    local user_key = 'user_holds:' .. user_id
    local ttl = redis.call('TTL', user_key)
    if ttl > 0 then
        redis.call('EXPIRE', user_key, ttl + extra_seconds)
    end

    return cjson.encode({extended = extended, not_owned = not_owned})
    """

    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        # Register Lua scripts
        self._acquire_script = self.redis.register_script(self.ACQUIRE_LOCKS_SCRIPT)
        self._release_script = self.redis.register_script(self.RELEASE_LOCKS_SCRIPT)
        self._extend_script = self.redis.register_script(self.EXTEND_LOCKS_SCRIPT)

    def _get_seat_key(self, showtime_id: int, seat_id: int) -> str:
        """Generate Redis key for a seat lock."""
        return f"{self.SEAT_LOCK_PREFIX}:{showtime_id}:{seat_id}"

    def _get_user_holds_key(self, user_id: str) -> str:
        """Generate Redis key for user's holds tracking."""
        return f"{self.USER_HOLDS_PREFIX}:{user_id}"

    def _get_seat_keys(self, showtime_id: int, seat_ids: list[int]) -> list[str]:
        """Generate Redis keys for multiple seats."""
        return [self._get_seat_key(showtime_id, sid) for sid in seat_ids]

    def _seat_ids_to_string(self, seat_ids: list[int]) -> str:
        """Convert seat IDs to comma-separated string for Lua script."""
        return ",".join(str(sid) for sid in seat_ids)

    async def acquire_locks(
        self,
        seat_ids: list[int],
        showtime_id: int,
        user_id: UUID,
        ttl: int = SEAT_HOLD_TTL,
    ) -> tuple[bool, list[int]]:
        """
        Atomically acquire locks for multiple seats.

        Args:
            seat_ids: List of seat IDs to lock
            showtime_id: The showtime these seats belong to
            user_id: The user acquiring the locks
            ttl: Lock time-to-live in seconds (default: 600)

        Returns:
            Tuple of (success: bool, failed_seat_ids: list[int])
            If success is True, failed_seat_ids will be empty.
            If success is False, failed_seat_ids contains seats that couldn't be locked.
        """
        if not seat_ids:
            return True, []

        keys = self._get_seat_keys(showtime_id, seat_ids)
        seat_ids_str = self._seat_ids_to_string(seat_ids)
        timestamp = str(int(time.time()))

        result = await self._acquire_script(
            keys=keys,
            args=[
                seat_ids_str,
                str(user_id),
                timestamp,
                str(ttl),
                str(showtime_id),
            ],
        )

        result_data = json.loads(result)
        return result_data["success"], result_data.get("failed_seats", [])

    async def release_locks(
        self,
        seat_ids: list[int],
        showtime_id: int,
        user_id: UUID,
    ) -> tuple[int, int]:
        """
        Release locks for multiple seats (only if owned by user).

        Args:
            seat_ids: List of seat IDs to unlock
            showtime_id: The showtime these seats belong to
            user_id: The user releasing the locks

        Returns:
            Tuple of (released_count: int, not_owned_count: int)
        """
        if not seat_ids:
            return 0, 0

        keys = self._get_seat_keys(showtime_id, seat_ids)
        seat_ids_str = self._seat_ids_to_string(seat_ids)

        result = await self._release_script(
            keys=keys,
            args=[seat_ids_str, str(user_id), str(showtime_id)],
        )

        result_data = json.loads(result)
        return result_data["released"], result_data["not_owned"]

    async def extend_locks(
        self,
        seat_ids: list[int],
        showtime_id: int,
        user_id: UUID,
        extra_seconds: int = 300,
    ) -> tuple[int, int]:
        """
        Extend the TTL for locked seats (only if owned by user).

        Args:
            seat_ids: List of seat IDs to extend
            showtime_id: The showtime these seats belong to
            user_id: The user extending the locks
            extra_seconds: Additional seconds to add to TTL

        Returns:
            Tuple of (extended_count: int, not_owned_count: int)
        """
        if not seat_ids:
            return 0, 0

        keys = self._get_seat_keys(showtime_id, seat_ids)
        seat_ids_str = self._seat_ids_to_string(seat_ids)

        result = await self._extend_script(
            keys=keys,
            args=[
                seat_ids_str,
                str(user_id),
                str(extra_seconds),
                str(showtime_id),
            ],
        )

        result_data = json.loads(result)
        return result_data["extended"], result_data["not_owned"]

    async def check_locks(
        self,
        seat_ids: list[int],
        showtime_id: int,
    ) -> dict[int, Optional[str]]:
        """
        Check who holds locks for specific seats.

        Args:
            seat_ids: List of seat IDs to check
            showtime_id: The showtime these seats belong to

        Returns:
            Dict mapping seat_id to holder_user_id (or None if not locked)
        """
        if not seat_ids:
            return {}

        keys = self._get_seat_keys(showtime_id, seat_ids)
        result = {}

        for i, seat_id in enumerate(seat_ids):
            key = keys[i]
            data = await self.redis.get(key)
            if data:
                parsed = json.loads(data)
                result[seat_id] = parsed.get("user_id")
            else:
                result[seat_id] = None

        return result

    async def get_user_holds(
        self,
        user_id: UUID,
    ) -> list[tuple[int, int]]:
        """
        Get all seat holds owned by a user.

        Returns:
            List of (showtime_id, seat_id) tuples
        """
        user_key = self._get_user_holds_key(str(user_id))
        holds = await self.redis.smembers(user_key)

        result = []
        for hold_key in holds:
            parts = hold_key.split(":")
            if len(parts) == 2:
                try:
                    showtime_id = int(parts[0])
                    seat_id = int(parts[1])
                    result.append((showtime_id, seat_id))
                except ValueError:
                    continue

        return result

    async def get_remaining_ttl(
        self,
        seat_ids: list[int],
        showtime_id: int,
        user_id: UUID,
    ) -> dict[int, int]:
        """
        Get remaining TTL for locked seats.

        Returns:
            Dict mapping seat_id to remaining seconds
        """
        if not seat_ids:
            return {}

        keys = self._get_seat_keys(showtime_id, seat_ids)
        result = {}

        for i, seat_id in enumerate(seat_ids):
            key = keys[i]
            ttl = await self.redis.ttl(key)
            # Verify user owns this lock
            data = await self.redis.get(key)
            if data:
                parsed = json.loads(data)
                if parsed.get("user_id") == str(user_id) and ttl > 0:
                    result[seat_id] = ttl

        return result
