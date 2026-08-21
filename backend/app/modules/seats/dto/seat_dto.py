"""Seat DTOs for API requests and responses."""
from typing import List
from pydantic import BaseModel, ConfigDict
from app.models.seat import SeatStatus


class SeatResponse(BaseModel):
    """Single seat response schema."""
    id: int
    showtime_id: int
    seat_label: str
    status: SeatStatus

    model_config = ConfigDict(from_attributes=True)


class SeatListResponse(BaseModel):
    """Response containing all seats for a showtime."""
    seats: List[SeatResponse]
    total: int


class HoldSeatsRequest(BaseModel):
    """Request to hold seats temporarily."""
    seat_ids: List[int]
    showtime_id: int


class ReleaseSeatsRequest(BaseModel):
    """Request to release held seats."""
    seat_ids: List[int]
    showtime_id: int


class SeatActionResponse(BaseModel):
    """Response for hold/release actions."""
    success: bool
    message: str
    released_seats: List[SeatResponse]
