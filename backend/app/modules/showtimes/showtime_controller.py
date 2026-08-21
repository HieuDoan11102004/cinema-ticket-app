"""Showtime API endpoints."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.shared.db.database import get_db
from app.modules.showtimes.showtime_service import ShowtimeService
from app.modules.showtimes.dto.showtime_dto import ShowtimeResponse, ShowtimeListResponse

router = APIRouter(prefix="/api/v1", tags=["showtimes"])


def get_showtime_service(db: Session = Depends(get_db)) -> ShowtimeService:
    """Dependency to get showtime service."""
    return ShowtimeService(db)


@router.get("/films/{film_id}/showtimes", response_model=ShowtimeListResponse)
def get_film_showtimes(
    film_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    upcoming_only: bool = True,
    service: ShowtimeService = Depends(get_showtime_service),
):
    """
    Get showtimes for a specific film.

    - **film_id**: The ID of the film
    - **skip**: Number of records to skip (pagination)
    - **limit**: Maximum number of records to return
    - **upcoming_only**: If true, only return future showtimes (default: true)
    """
    showtimes, total = service.get_showtimes_for_film(
        film_id=film_id,
        skip=skip,
        limit=limit,
        upcoming_only=upcoming_only,
    )
    return ShowtimeListResponse(showtimes=showtimes, total=total)


@router.get("/showtimes/{showtime_id}", response_model=ShowtimeResponse)
def get_showtime(
    showtime_id: int,
    service: ShowtimeService = Depends(get_showtime_service),
):
    """
    Get a single showtime by ID.

    - **showtime_id**: The ID of the showtime
    """
    showtime = service.get_showtime_by_id(showtime_id)
    if not showtime:
        raise HTTPException(status_code=404, detail="Showtime not found")
    return showtime


@router.get("/showtimes", response_model=ShowtimeListResponse)
def get_all_showtimes(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    upcoming_only: bool = True,
    service: ShowtimeService = Depends(get_showtime_service),
):
    """
    Get all showtimes.

    - **skip**: Number of records to skip (pagination)
    - **limit**: Maximum number of records to return
    - **upcoming_only**: If true, only return future showtimes (default: true)
    """
    showtimes, total = service.get_all_showtimes(
        skip=skip,
        limit=limit,
        upcoming_only=upcoming_only,
    )
    return ShowtimeListResponse(showtimes=showtimes, total=total)
