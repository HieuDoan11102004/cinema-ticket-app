"""Payment API endpoints."""
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session

from app.modules.payments.payment_service import PaymentService
from app.modules.payments.payment_repository import PaymentRepository
from app.modules.payments.dto.payment_dto import (
    CreateCheckoutRequest,
    CheckoutResponse,
    PaymentResponse,
    WebhookResponse,
)
from app.modules.auth.auth_controller import get_current_user_id
from app.shared.db.database import get_db

router = APIRouter(prefix="/api/v1/payments", tags=["payments"])


def get_payment_service(db: Session = Depends(get_db)) -> PaymentService:
    """Dependency to get payment service."""
    return PaymentService(db)


@router.post(
    "/create-checkout",
    response_model=CheckoutResponse,
    responses={
        400: {"description": "Invalid booking or payment already processed"},
        401: {"description": "Not authenticated"},
        404: {"description": "Booking not found"},
    },
)
def create_checkout(
    request: CreateCheckoutRequest,
    user_id: uuid.UUID = Depends(get_current_user_id),
    service: PaymentService = Depends(get_payment_service),
) -> CheckoutResponse:
    """
    Create a payment checkout session for a booking.

    Returns a checkout URL where the user can complete payment.

    - **booking_id**: The booking ID to create payment for
    """
    result = service.create_checkout(user_id, request)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not create checkout. Booking may not exist, not belong to you, or already be paid.",
        )
    return result


@router.get(
    "/{payment_id}",
    response_model=PaymentResponse,
    responses={
        401: {"description": "Not authenticated"},
        404: {"description": "Payment not found"},
    },
)
def get_payment(
    payment_id: int,
    user_id: uuid.UUID = Depends(get_current_user_id),
    service: PaymentService = Depends(get_payment_service),
) -> PaymentResponse:
    """Get payment details by ID."""
    payment = service.get_payment(payment_id)
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found",
        )
    return payment


@router.post(
    "/webhook",
    response_model=WebhookResponse,
    responses={400: {"description": "Invalid webhook data"}},
)
def payment_webhook(
    payment_id: int,
    provider: str,
    status: str,
    transaction_id: Optional[str] = None,
    service: PaymentService = Depends(get_payment_service),
) -> WebhookResponse:
    """
    Handle payment provider webhook callbacks.

    This endpoint is called by the payment provider (Stripe/VNPay/MoMo)
    to notify us of payment status changes.

    - **payment_id**: Our internal payment ID
    - **provider**: Payment provider name (stripe, vnpay, momo)
    - **status**: Status from the provider
    - **transaction_id**: Provider's transaction ID (optional)
    """
    return service.process_webhook(payment_id, provider, status, transaction_id)


# Mock checkout endpoint for testing (remove in production)
@router.post(
    "/mock-checkout/{payment_id}/complete",
    response_model=PaymentResponse,
    responses={
        400: {"description": "Payment already processed"},
        404: {"description": "Payment not found"},
    },
)
def mock_checkout_complete(
    payment_id: int,
    user_id: uuid.UUID = Depends(get_current_user_id),
    service: PaymentService = Depends(get_payment_service),
) -> PaymentResponse:
    """
    Mock endpoint to simulate successful payment completion.

    **FOR TESTING ONLY** - In production, users would be redirected to
    the payment provider's page and the webhook would be called automatically.

    - **payment_id**: The payment ID to mark as complete
    """
    payment = service.confirm_payment(payment_id)
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found or already processed",
        )
    return payment


@router.post(
    "/mock-checkout/{payment_id}/fail",
    response_model=PaymentResponse,
    responses={
        400: {"description": "Payment already processed"},
        404: {"description": "Payment not found"},
    },
)
def mock_checkout_fail(
    payment_id: int,
    user_id: uuid.UUID = Depends(get_current_user_id),
    service: PaymentService = Depends(get_payment_service),
) -> PaymentResponse:
    """
    Mock endpoint to simulate failed payment.

    **FOR TESTING ONLY**

    - **payment_id**: The payment ID to mark as failed
    """
    payment = service.fail_payment(payment_id)
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found or already processed",
        )
    return payment
