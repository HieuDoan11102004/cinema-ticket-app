"""Add booking_code, total_price, expires_at to bookings

Revision ID: abc123def456
Revises: 1b629e476999
Create Date: 2026-08-21

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'abc123def456'
down_revision: Union[str, Sequence[str], None] = '1b629e476999'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add booking fields to bookings table."""
    # Add booking_code column
    op.add_column('bookings', sa.Column('booking_code', sa.String(20), nullable=True))
    op.create_index('ix_bookings_booking_code', 'bookings', ['booking_code'], unique=True)

    # Add total_price column
    op.add_column('bookings', sa.Column('total_price', sa.Numeric(10, 2), nullable=True))

    # Add expires_at column
    op.add_column('bookings', sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True))

    # Add cancelled_at column
    op.add_column('bookings', sa.Column('cancelled_at', sa.DateTime(timezone=True), nullable=True))

    # Add cancellation_reason column
    op.add_column('bookings', sa.Column('cancellation_reason', sa.String(500), nullable=True))

    # Make existing bookings nullable and set defaults for data integrity
    # (In production, you'd want to handle existing data)


def downgrade() -> None:
    """Remove booking fields from bookings table."""
    op.drop_column('bookings', 'cancellation_reason')
    op.drop_column('bookings', 'cancelled_at')
    op.drop_column('bookings', 'expires_at')
    op.drop_column('bookings', 'total_price')
    op.drop_index('ix_bookings_booking_code', 'bookings')
    op.drop_column('bookings', 'booking_code')
