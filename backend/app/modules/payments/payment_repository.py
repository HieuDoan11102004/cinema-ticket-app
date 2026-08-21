"""Payment repository for database operations."""
from typing import Optional
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.payment import Payment, PaymentStatus


class PaymentRepository:
    """Repository for Payment database operations."""

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, payment_id: int) -> Optional[Payment]:
        """Get payment by ID."""
        stmt = (
            select(Payment)
            .options(joinedload(Payment.booking))
            .where(Payment.id == payment_id)
        )
        return self.db.scalars(stmt).first()

    def get_by_booking_id(self, booking_id: int) -> Optional[Payment]:
        """Get payment for a specific booking."""
        stmt = (
            select(Payment)
            .options(joinedload(Payment.booking))
            .where(Payment.booking_id == booking_id)
        )
        return self.db.scalars(stmt).first()

    def create(
        self,
        booking_id: int,
        provider: str,
        amount: float,
    ) -> Payment:
        """Create a new payment record."""
        payment = Payment(
            booking_id=booking_id,
            provider=provider,
            status=PaymentStatus.PENDING,
            amount=amount,
        )
        self.db.add(payment)
        self.db.commit()
        self.db.refresh(payment)
        return payment

    def update_status(self, payment_id: int, status: PaymentStatus) -> Optional[Payment]:
        """Update payment status."""
        payment = self.get_by_id(payment_id)
        if not payment:
            return None

        payment.status = status
        self.db.commit()
        self.db.refresh(payment)
        return payment
