"""Payment DTOs for API requests and responses."""
from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, ConfigDict
from app.models.payment import PaymentStatus, PaymentProvider


class CreateCheckoutRequest(BaseModel):
    """Request to create a payment checkout session."""
    booking_id: int


class CheckoutResponse(BaseModel):
    """Response containing payment checkout URL."""
    checkout_url: str
    payment_id: int
    amount: Decimal
    provider: PaymentProvider
    expires_at: datetime


class PaymentResponse(BaseModel):
    """Payment status response."""
    id: int
    booking_id: int
    provider: PaymentProvider
    status: PaymentStatus
    amount: Decimal
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class WebhookResponse(BaseModel):
    """Response for webhook calls."""
    success: bool
    message: str
