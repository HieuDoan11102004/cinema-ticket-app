"""Payment service for business logic."""
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.modules.payments.payment_repository import PaymentRepository
from app.modules.payments.dto.payment_dto import (
    CreateCheckoutRequest,
    CheckoutResponse,
    PaymentResponse,
    WebhookResponse,
)
from app.modules.bookings.booking_repository import BookingRepository
from app.modules.bookings.booking_service import BookingService
from app.models.payment import Payment, PaymentProvider, PaymentStatus
from app.models.booking import BookingStatus


class PaymentService:
    """Service for payment operations."""

    # Checkout session expires after 10 minutes (same as booking)
    CHECKOUT_EXPIRY_MINUTES = 10

    def __init__(self, db: Session):
        self.db = db
        self.repository = PaymentRepository(db)
        self.booking_repository = BookingRepository(db)
        self.booking_service = BookingService(db)

    def _to_response(self, payment: Payment) -> PaymentResponse:
        """Convert payment model to response DTO."""
        return PaymentResponse(
            id=payment.id,
            booking_id=payment.booking_id,
            provider=payment.provider,
            status=payment.status,
            amount=Decimal(str(payment.amount)),
            created_at=payment.created_at,
            updated_at=payment.updated_at,
        )

    def create_checkout(
        self,
        user_id: UUID,
        request: CreateCheckoutRequest,
    ) -> Optional[CheckoutResponse]:
        """
        Create a payment checkout session.

        Flow:
        1. Validate booking exists and belongs to user
        2. Validate booking is in PENDING status
        3. Check no existing payment for this booking
        4. Create payment record
        5. Return checkout URL (mocked for now - real implementation would call payment provider)
        """
        # Get booking
        booking = self.booking_repository.get_by_id(request.booking_id)
        if not booking:
            return None

        # Ensure user owns this booking
        if booking.user_id != user_id:
            return None

        # Validate booking is PENDING
        if booking.status != BookingStatus.PENDING:
            return None

        # Check if payment already exists
        existing_payment = self.repository.get_by_booking_id(request.booking_id)
        if existing_payment:
            # Return existing checkout if still valid
            if existing_payment.status == PaymentStatus.PENDING:
                return CheckoutResponse(
                    checkout_url=self._get_mock_checkout_url(existing_payment.id),
                    payment_id=existing_payment.id,
                    amount=Decimal(str(existing_payment.amount)),
                    provider=existing_payment.provider,
                    expires_at=booking.expires_at or datetime.now(timezone.utc),
                )
            return None

        # Create payment record
        # Default to Stripe for now
        payment = self.repository.create(
            booking_id=request.booking_id,
            provider=PaymentProvider.STRIPE.value,
            amount=float(booking.total_price),
        )

        # Calculate expiry
        expires_at = booking.expires_at or (datetime.now(timezone.utc) + timedelta(minutes=self.CHECKOUT_EXPIRY_MINUTES))

        return CheckoutResponse(
            checkout_url=self._get_mock_checkout_url(payment.id),
            payment_id=payment.id,
            amount=Decimal(str(payment.amount)),
            provider=PaymentProvider(payment.provider),
            expires_at=expires_at,
        )

    def _get_mock_checkout_url(self, payment_id: int) -> str:
        """Generate a mock checkout URL. Replace with real payment provider integration."""
        # In production, this would create a Stripe/VNPay/MoMo checkout session
        # and return the actual payment URL
        return f"/api/v1/payments/mock-checkout/{payment_id}"

    def process_webhook(
        self,
        payment_id: int,
        provider: str,
        status: str,
        transaction_id: Optional[str] = None,
    ) -> WebhookResponse:
        """
        Process a payment webhook from the payment provider.

        Flow:
        1. Validate payment exists
        2. Update payment status based on provider callback
        3. If successful, confirm the booking
        """
        payment = self.repository.get_by_id(payment_id)
        if not payment:
            return WebhookResponse(
                success=False,
                message="Payment not found",
            )

        # Validate provider matches
        if payment.provider != provider:
            return WebhookResponse(
                success=False,
                message="Provider mismatch",
            )

        # Map provider status to our PaymentStatus
        payment_status = self._map_provider_status(provider, status)
        if not payment_status:
            return WebhookResponse(
                success=False,
                message=f"Unknown status from {provider}: {status}",
            )

        # Update payment status
        self.repository.update_status(payment_id, payment_status)

        # If payment succeeded, confirm the booking
        if payment_status == PaymentStatus.SUCCEEDED:
            self.booking_service.confirm_booking(payment.booking_id)

        return WebhookResponse(
            success=True,
            message="Payment status updated",
        )

    def _map_provider_status(self, provider: str, status: str) -> Optional[PaymentStatus]:
        """Map payment provider status to our PaymentStatus enum."""
        # Stripe status mapping
        if provider == PaymentProvider.STRIPE.value:
            status_lower = status.lower()
            if status_lower in ("succeeded", "paid", "complete"):
                return PaymentStatus.SUCCEEDED
            elif status_lower in ("failed", "cancelled", "expired"):
                return PaymentStatus.FAILED
            elif status_lower in ("refunded", "refund"):
                return PaymentStatus.REFUNDED
            elif status_lower in ("pending", "processing"):
                return PaymentStatus.PENDING

        # VNPay status mapping
        elif provider == PaymentProvider.VNPAY.value:
            status_code = status  # VNPay uses numeric codes
            if status_code == "00":
                return PaymentStatus.SUCCEEDED
            elif status_code in ("01", "02", "03", "04", "05", "06", "07", "08", "09"):
                return PaymentStatus.FAILED

        # MoMo status mapping
        elif provider == PaymentProvider.MOMO.value:
            if status in ("0", "成功"):
                return PaymentStatus.SUCCEEDED
            elif status in ("0", "Thành công"):
                return PaymentStatus.SUCCEEDED

        return None

    def get_payment(self, payment_id: int) -> Optional[PaymentResponse]:
        """Get payment details by ID."""
        payment = self.repository.get_by_id(payment_id)
        if not payment:
            return None
        return self._to_response(payment)

    def confirm_payment(self, payment_id: int) -> Optional[PaymentResponse]:
        """Manually confirm a payment (for testing/mock checkout)."""
        payment = self.repository.update_status(payment_id, PaymentStatus.SUCCEEDED)
        if not payment:
            return None

        # Confirm the booking
        self.booking_service.confirm_booking(payment.booking_id)

        return self._to_response(payment)

    def fail_payment(self, payment_id: int) -> Optional[PaymentResponse]:
        """Mark a payment as failed."""
        payment = self.repository.update_status(payment_id, PaymentStatus.FAILED)
        if not payment:
            return None
        return self._to_response(payment)
