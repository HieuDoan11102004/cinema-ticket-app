from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.shared.redis import redis_client
from app.modules.auth.auth_controller import router as auth_router
from app.modules.films.film_controller import router as film_router
from app.modules.seats.seat_controller import router as seat_router
from app.modules.showtimes.showtime_controller import router as showtime_router
from app.modules.bookings.booking_controller import router as booking_router
from app.modules.payments.payment_controller import router as payment_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle - startup and shutdown."""
    # Startup: connect to Redis
    await redis_client.connect()
    yield
    # Shutdown: disconnect from Redis
    await redis_client.disconnect()


app = FastAPI(title="CineBook API", version="1.0.0", lifespan=lifespan)

# CORS middleware for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(film_router)
app.include_router(seat_router)
app.include_router(showtime_router)
app.include_router(booking_router)
app.include_router(payment_router)


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    redis_ok = await redis_client.health_check()
    return {
        "status": "ok" if redis_ok else "degraded",
        "redis": "connected" if redis_ok else "disconnected"
    }
