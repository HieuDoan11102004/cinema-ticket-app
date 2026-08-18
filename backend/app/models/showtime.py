from sqlalchemy import Column, Integer, String, DateTime, Numeric, ForeignKey
from sqlalchemy.orm import relationship
from app.shared.db.database import Base


class Showtime(Base):
    __tablename__ = "showtimes"

    id = Column(Integer, primary_key=True, index=True)
    film_id = Column(Integer, ForeignKey("films.id"), nullable=False)
    cinema_room = Column(String, nullable=False)
    start_time = Column(DateTime, nullable=False)
    base_price = Column(Numeric(10, 2), nullable=False)

    # Relationships
    film = relationship("Film", backref="showtimes")
    seats = relationship("Seat", back_populates="showtime")
    bookings = relationship("Booking", back_populates="showtime")
