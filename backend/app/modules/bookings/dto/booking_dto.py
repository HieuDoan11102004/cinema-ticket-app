"""Booking DTOs for API requests and responses."""
from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, ConfigDict
from app.models.booking import BookingStatus
from app.modules.seats.dto.seat_dto import SeatResponse


class CreateBookingRequest(BaseModel):
    """Request to create a new booking from held seats."""
    seat_ids: List[int]
    showtime_id: int


class BookingSeatResponse(BaseModel):
    """Booking seat with seat details."""
    id: int
    seat_id: int
    seat_label: str
    status: str

    model_config = ConfigDict(from_attributes=True)


class BookingResponse(BaseModel):
    """Single booking response schema."""
    id: int
    user_id: str
    showtime_id: int
    booking_code: str
    total_price: Decimal
    status: BookingStatus
    expires_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    cancellation_reason: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    seats: List[SeatResponse] = []

    model_config = ConfigDict(from_attributes=True)


class BookingListResponse(BaseModel):
    """Response containing user's bookings."""
    bookings: List[BookingResponse]
    total: int


class BookingActionResponse(BaseModel):
    """Response for booking actions (cancel, etc.)."""
    success: bool
    message: str
    booking: Optional[BookingResponse] = None
