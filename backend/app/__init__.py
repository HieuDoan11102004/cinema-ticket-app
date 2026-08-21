from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.modules.auth.auth_controller import router as auth_router
from app.modules.films.film_controller import router as film_router
from app.modules.showtimes.showtime_controller import router as showtime_router

app = FastAPI(title="CineBook API", version="1.0.0")

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
app.include_router(showtime_router)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
