# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**CineBook** is an Online Cinema Ticket Booking Platform with a FastAPI backend and Next.js frontend (frontend not yet implemented). The backend is in early development: ORM models are created and database seeding works, but API routes have not been implemented yet.

## Technology Stack

- **Backend**: FastAPI + SQLAlchemy 2.0 + Pydantic
- **Database**: PostgreSQL (via Docker Compose)
- **Migrations**: Alembic
- **Package Manager**: `uv` (not pip)
- **Python**: 3.11
- **Password Hashing**: bcrypt

## Common Commands

```bash
# Start PostgreSQL with Docker
docker-compose up -d db

# Initialize database tables (legacy, use Alembic instead)
cd backend && uv run python -m app.db.init_db

# Alembic migrations
cd backend && uv run alembic upgrade head        # Apply all migrations
cd backend && uv run alembic revision --autogenerate -m "description"  # Generate new migration
cd backend && uv run alembic downgrade -1        # Rollback one migration

# Seed database with fake data (20 users)
cd backend && uv run python -m app.db.seed

# Run the FastAPI app (once routes are implemented)
cd backend && uv run uvicorn app:app --reload

# Install dependencies
cd backend && uv sync

# Run tests
cd backend && uv run pytest

# Lint code
cd backend && uv run ruff check .
```

## Architecture

### Backend Structure (`backend/app/`)

```
app/
├── __main__.py          # Entry point: runs init_db()
├── db/
│   ├── database.py     # SQLAlchemy engine, SessionLocal, Base
│   ├── init_db.py      # Creates all tables
│   └── seed.py         # Seeds database with fake users (Faker)
├── models/             # SQLAlchemy ORM models
│   ├── user.py         # User model
│   ├── film.py         # Film model (with genres as PostgreSQL ARRAY)
│   ├── showtime.py    # Showtime model
│   ├── seat.py        # Seat model with status enum
│   ├── booking.py     # Booking + BookingSeat junction table
│   └── payment.py     # Payment model with provider/status enums
└── schemas/           # Pydantic models (not yet created)
```

### Database Models

The core entities follow this schema:

| Model | Purpose |
|-------|---------|
| `User` | Customer accounts with name, email, password_hash (bcrypt), phone, birth_date |
| `Film` | Movies with title, genres (ARRAY), overview, poster_url, tmdb_id |
| `Showtime` | Links films to rooms, times, and prices |
| `Seat` | Individual seats per showtime with status (available/held/booked) |
| `Booking` | Links user to showtime, holds booking_seats |
| `BookingSeat` | Junction table for many-to-many seats-per-booking |
| `Payment` | Payment records linked to bookings |

### Seat Locking Mechanism

The most critical feature is concurrent seat booking. The pattern (not yet implemented) will be:

1. User selects seats → backend checks status in Postgres
2. Backend writes short-lived hold keys to Redis (TTL ~10 minutes)
3. Payment success → seats marked 'booked' in Postgres, Redis hold cleared
4. TTL expires → hold auto-releases, seats available again
5. Background worker reconciles orphaned holds

**Key invariant**: A seat for a given showtime must never have two confirmed bookings.

### API Routes (Planned)

```
/api/v1/auth/*         # Authentication
/api/v1/films/*        # Film listing and details
/api/v1/showtimes/*    # Showtimes and seat maps
/api/v1/bookings/*     # Booking flow (hold → confirm)
/api/v1/payments/*    # Checkout and webhooks
/api/v1/recommendations # Film recommendations
/api/v1/chatbot/*      # AI chatbot
```

## Development Conventions

- **Database sessions**: Use `get_db()` dependency in FastAPI routes
- **Models**: All import from `app.models` to register with `Base.metadata`
- **Enums**: Python `enum.Enum` for statuses (BookingStatus, SeatStatus, PaymentStatus)
- **Seed data**: Uses Faker with Vietnamese locale (`Faker("vi_VN")`), seeded for reproducibility

## Current Development Phase

Phase 1 in progress: Database models and seed data are complete. Next steps are implementing API routes and authentication.

## Environment Variables

See `.env` for PostgreSQL connection:
```
POSTGRES_USER=user
POSTGRES_PASSWORD=123
POSTGRES_DB=cinema
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
```

## Test and Lint Configuration

Per project memory, use `pytest` for tests and `ruff check` for linting. These are not yet configured in the project.
