from sqlalchemy import Column, Integer, String, Text, Date, Float, ARRAY
from sqlalchemy.orm import relationship
from app.shared.db.database import Base


class Film(Base):
    __tablename__ = "films"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    genres = Column(ARRAY(String), default=[])  # PostgreSQL array for genres
    overview = Column(Text)
    poster_url = Column(String)
    duration_min = Column(Integer)
    release_date = Column(Date)
    tmdb_id = Column(Integer, unique=True, nullable=True)  # Reference to TMDB source data
