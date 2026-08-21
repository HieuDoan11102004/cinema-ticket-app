"""Seat DTOs for API requests and responses."""
from typing import List, Optional
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


class ExtendHoldRequest(BaseModel):
    """Request to extend seat hold duration."""
    seat_ids: List[int]
    showtime_id: int
    extra_seconds: Optional[int] = 300


class ReleaseSeatsRequest(BaseModel):
    """Request to release held seats."""
    seat_ids: List[int]
    showtime_id: int


class SeatActionResponse(BaseModel):
    """Response for hold/release actions."""
    success: bool
    message: str
    released_seats: List[SeatResponse] = []


class HoldExpiryResponse(BaseModel):
    """Response for extend hold action."""
    success: bool
    message: str
    extended_count: int
    remaining_seconds: int


class HoldStatusResponse(BaseModel):
    """Response for hold status check."""
    seats: dict[int, dict]
