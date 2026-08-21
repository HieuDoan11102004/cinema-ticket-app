# Plan: User Ticket Booking System

## Context

Users need to book movie tickets through the platform. The backend has all core models (Booking, BookingSeat, Payment, Seat with status enum) and the seats module already supports holding/releasing seats. What's missing is the bookings module to create/confirm/cancel bookings, and the payments module to process payments.

## Current State

| Component | Status |
|-----------|--------|
| Models (User, Film, Showtime, Seat, Booking, Payment) | ✅ Implemented |
| Seat holding/release (`POST /seats/hold`, `POST /seats/release`) | ✅ Implemented |
| Auth (JWT, login, signup) | ✅ Implemented |
| Films, Showtimes APIs | ✅ Implemented |
| **Bookings module** | ❌ Missing |
| **Payments module** | ❌ Missing |
| Booking model fields (booking_code, total_price, expires_at) | ⚠️ Partial |

## Implementation Approach

### Phase 1: Enhance Booking Model

Add missing fields to `backend/app/models/booking.py`:
- `booking_code` (String) - unique confirmation code for users
- `total_price` (Numeric) - calculated from seats + modifiers
- `expires_at` (DateTime) - auto-cancel timeout for PENDING bookings

### Phase 2: Create Bookings Module

Create `backend/app/modules/bookings/` with standard pattern:

**Files to create:**
- `dto/booking_dto.py` - Request/response schemas
- `booking_repository.py` - Database queries
- `booking_service.py` - Business logic
- `booking_controller.py` - FastAPI routes

**Endpoints:**
```
POST   /api/v1/bookings              - Create booking from held seats
GET    /api/v1/bookings              - List user's bookings
GET    /api/v1/bookings/{booking_id} - Get booking details
POST   /api/v1/bookings/{booking_id}/cancel - Cancel booking
```

**Booking flow:**
1. User selects seats → `POST /seats/hold` (existing)
2. User confirms → `POST /bookings` creates PENDING booking, links seats
3. User pays → Payment succeeds → booking status → CONFIRMED, seats → BOOKED
4. On timeout or cancel → seats released, booking → CANCELLED

### Phase 3: Create Payments Module

Create `backend/app/modules/payments/` with standard pattern:

**Files to create:**
- `dto/payment_dto.py` - Request/response schemas
- `payment_repository.py` - Database queries
- `payment_service.py` - Business logic
- `payment_controller.py` - FastAPI routes

**Endpoints:**
```
POST   /api/v1/payments/create-checkout  - Create payment session
POST   /api/v1/payments/webhook          - Handle payment provider callbacks
GET    /api/v1/payments/{payment_id}     - Get payment status
```

**Payment flow:**
1. Create checkout → returns payment URL (Stripe/VNPay/MoMo)
2. User pays on provider's page
3. Webhook receives success → update booking to CONFIRMED, seats to BOOKED

### Phase 4: Register Routes

Update `backend/app/__init__.py` to include:
```python
from app.modules.bookings.booking_controller import router as booking_router
from app.modules.payments.payment_controller import router as payment_router
app.include_router(booking_router, prefix="/api/v1")
app.include_router(payment_router, prefix="/api/v1")
```

### Phase 5: Database Migration

Generate Alembic migration for new model fields:
```bash
cd backend && uv run alembic revision --autogenerate -m "Add booking_code and total_price to bookings"
```

## Critical Files to Modify/Create

| File | Action |
|------|--------|
| `backend/app/models/booking.py` | Add fields: booking_code, total_price, expires_at |
| `backend/app/modules/bookings/dto/booking_dto.py` | Create |
| `backend/app/modules/bookings/booking_repository.py` | Create |
| `backend/app/modules/bookings/booking_service.py` | Create |
| `backend/app/modules/bookings/booking_controller.py` | Create |
| `backend/app/modules/payments/dto/payment_dto.py` | Create |
| `backend/app/modules/payments/payment_repository.py` | Create |
| `backend/app/modules/payments/payment_service.py` | Create |
| `backend/app/modules/payments/payment_controller.py` | Create |
| `backend/app/__init__.py` | Add router registrations |

## Verification

1. **Unit tests**: `cd backend && uv run pytest`
2. **Manual API test**:
   - Create user via `/api/v1/auth/signup`
   - Login via `/api/v1/auth/login`
   - Get showtime via `/api/v1/films/{id}/showtimes`
   - Hold seats via `/api/v1/seats/hold`
   - Create booking via `/api/v1/bookings`
   - Check booking status via `/api/v1/bookings/{id}`
   - Cancel booking via `/api/v1/bookings/{id}/cancel`

## Dependencies

- Uses existing `get_db()` dependency
- Uses existing `get_current_user_id` for auth
- No new packages needed for MVP (Stripe integration can be mocked)

## Future Enhancements (Out of Scope)

- Redis for distributed seat locking
- Background worker for expired booking cleanup
- Email/SMS notifications
- Promo codes
- Seat type pricing (VIP, standard)
