from sqlalchemy import Column, Integer, String, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from app.db.database import Base
import enum


class SeatStatus(str, enum.Enum):
    AVAILABLE = "available"
    HELD = "held"
    BOOKED = "booked"


class Seat(Base):
    __tablename__ = "seats"

    id = Column(Integer, primary_key=True, index=True)
    showtime_id = Column(Integer, ForeignKey("showtimes.id"), nullable=False)
    seat_label = Column(String, nullable=False)  # e.g., 'A5'
    status = Column(SQLEnum(SeatStatus), default=SeatStatus.AVAILABLE, nullable=False)

    # Relationships
    showtime = relationship("Showtime", back_populates="seats")
    booking_seats = relationship("BookingSeat", back_populates="seat")
