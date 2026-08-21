# Plan: Redis Seat Locking for Concurrent Booking ✅ IMPLEMENTED

## Context

The current seat holding implementation had a **race condition vulnerability**. When `seat_service.py:hold_seats()` was called:

1. It reads seats from Postgres to check availability
2. Then updates them to HELD

Two concurrent requests could both see seats as AVAILABLE before either writes, causing double-booking.

Redis now provides **atomic distributed locks** with TTL so holds auto-expire, preventing this race condition.

## Current Architecture

```
Seat Model: AVAILABLE → HELD → BOOKED (or back to AVAILABLE on cancel)
Booking Model: PENDING (10 min expiry) → CONFIRMED
Payment: Webhook → confirm_payment() → confirm_booking() → seats → BOOKED
```

## Implementation Complete ✅

### Phase 1: Infrastructure ✅

1. ✅ **Add Redis to Docker Compose** (`docker-compose.yml`)
   - Redis 7 Alpine image with persistence
   - Port 6379 exposed
   - Volume for data persistence

2. ✅ **Add Redis dependency** (`backend/pyproject.toml`)
   - `redis>=5.0.0`

3. ✅ **Add Redis config** (`backend/app/shared/core/config.py`)
   - `REDIS_HOST`, `REDIS_PORT`, `REDIS_PASSWORD` from `.env`
   - `REDIS_URL` for connection
   - `SEAT_HOLD_TTL` = 600 seconds

4. ✅ **Create Redis client** (`backend/app/shared/redis/client.py`)
   - `redis.asyncio` for async Redis (FastAPI compatible)
   - Connection pool pattern
   - Health check utility

### Phase 2: Redis Lock Service ✅

5. ✅ **Create seat lock service** (`backend/app/modules/seats/seat_lock_service.py`)

   Key design:
   - Key format: `seat_lock:{showtime_id}:{seat_id}`
   - Value: JSON `{"user_id": "...", "timestamp": "...", "showtime_id": "..."}`
   - TTL: 600 seconds (10 minutes)

   Methods:
   ```python
   async def acquire_locks(seat_ids, showtime_id, user_id)
   async def release_locks(seat_ids, showtime_id, user_id)
   async def extend_locks(seat_ids, showtime_id, user_id, extra_seconds)
   async def check_locks(seat_ids, showtime_id)
   async def get_user_holds(user_id)
   async def get_remaining_ttl(seat_ids, showtime_id, user_id)
   ```

   Uses Lua scripts for atomic multi-key operations:
   - `ACQUIRE_LOCKS_SCRIPT` - atomically check and acquire all locks
   - `RELEASE_LOCKS_SCRIPT` - atomically release owned locks
   - `EXTEND_LOCKS_SCRIPT` - atomically extend owned locks

### Phase 3: Hybrid Lock Check ✅

6. ✅ **Update SeatService** (`backend/app/modules/seats/seat_service.py`)

   Modified `hold_seats()`:
   1. Check Postgres (fast rejection for BOOKED seats)
   2. Try Redis atomic lock for ALL seats
   3. If Redis succeeds, update Postgres to HELD
   4. Return failure if any Redis lock fails

   Modified `release_seats()`:
   1. Verify user owns the locks in Redis
   2. Update Postgres to AVAILABLE
   3. Release Redis locks

### Phase 4: Background Cleanup Worker ✅

7. ✅ **Create Redis hold expiry handler** (`backend/app/modules/seats/seat_lock_worker.py`)

   - Polls every 30 seconds for orphaned holds
   - Releases seats marked HELD in Postgres with no Redis lock
   - Can be run as separate process

8. ✅ **Update BookingService** (`backend/app/modules/bookings/booking_service.py`)

   Modified `create_booking()`:
   - Verifies user owns Redis locks for held seats
   - Clears Redis locks when booking is created (seats now tied to booking)

   Modified `cancel_booking()`:
   - Releases Redis locks for the cancelled seats

### Phase 5: API Updates ✅

9. ✅ **Update seat controller** (`backend/app/modules/seats/seat_controller.py`)
   - Pass `user_id` to hold/release (requires auth)
   - Add `POST /seats/extend` to extend hold TTL
   - Add `GET /seats/status` to check hold status

10. ✅ **Update DTOs** (`backend/app/modules/seats/dto/seat_dto.py`)
    - `HoldSeatsRequest` - requires user context (from auth)
    - `ExtendHoldRequest` - for extending hold duration
    - `HoldExpiryResponse` - for remaining time
    - `HoldStatusResponse` - for status check

## Files Created/Modified

| File | Status |
|------|--------|
| `docker-compose.yml` | ✅ Modified - Redis service added |
| `.env` | ✅ Modified - Redis config added |
| `backend/pyproject.toml` | ✅ Modified - redis dependency added |
| `backend/app/shared/core/config.py` | ✅ Modified - Redis config added |
| `backend/app/shared/redis/client.py` | ✅ NEW - Redis client |
| `backend/app/shared/redis/__init__.py` | ✅ NEW - Redis module init |
| `backend/app/modules/seats/seat_lock_service.py` | ✅ NEW - Redis lock logic |
| `backend/app/modules/seats/seat_lock_worker.py` | ✅ NEW - Expiry handler |
| `backend/app/modules/seats/seat_service.py` | ✅ Modified - Redis locking |
| `backend/app/modules/seats/seat_controller.py` | ✅ Modified - async + auth |
| `backend/app/modules/seats/dto/seat_dto.py` | ✅ Modified - Extended DTOs |
| `backend/app/modules/bookings/booking_service.py` | ✅ Modified - Redis integration |
| `backend/app/modules/bookings/booking_controller.py` | ✅ Modified - async methods |
| `backend/app/__init__.py` | ✅ Modified - Redis lifespan |

## Redis Key Schema

```
seat_lock:{showtime_id}:{seat_id} = '{"user_id":"...", "timestamp":..., "showtime_id":...}'  TTL=600s
user_holds:{user_id} = set of "showtime_id:seat_id"                                        TTL=600s
```

## Testing

1. Start Redis: `docker compose up -d redis`
2. Run the app: `cd backend && uv run uvicorn app:app --reload`
3. Test manual flow:
   ```bash
   # Login to get token
   curl -X POST http://localhost:8000/api/v1/auth/login \
     -H "Content-Type: application/json" \
     -d '{"email": "test@example.com", "password": "password"}'

   # Hold seats (requires auth)
   curl -X POST http://localhost:8000/api/v1/seats/hold \
     -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"seat_ids": [1, 2], "showtime_id": 1}'

   # Check hold status
   curl "http://localhost:8000/api/v1/seats/status?seat_ids=1&seat_ids=2&showtime_id=1" \
     -H "Authorization: Bearer $TOKEN"

   # Release seats
   curl -X POST http://localhost:8000/api/v1/seats/release \
     -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"seat_ids": [1, 2], "showtime_id": 1}'
   ```
