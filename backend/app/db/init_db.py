# Import all models to register them with Base.metadata
from app.models import (
    User,
    Film,
    Showtime,
    Seat,
    SeatStatus,
    Booking,
    BookingSeat,
    BookingStatus,
    Payment,
    PaymentProvider,
    PaymentStatus,
)
from app.db.database import Base, engine


def init_db():
    """Create all tables in PostgreSQL"""
    # This imports the database engine from database.py
    Base.metadata.create_all(bind=engine)
    print("✅ All tables created successfully!")


if __name__ == "__main__":
    init_db()
