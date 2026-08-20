from sqlalchemy import Column, Integer, String, Text, Date, Float, ARRAY, Boolean, BigInteger
from sqlalchemy.orm import relationship
from app.shared.db.database import Base


class Film(Base):
    __tablename__ = "films"

    id = Column(Integer, primary_key=True, index=True)

    # Basic Info
    title = Column(String, nullable=False)
    original_title = Column(String)
    tagline = Column(String)
    overview = Column(Text)
    release_date = Column(Date)

    # Media
    poster_url = Column(String)
    backdrop_url = Column(String)
    trailer_url = Column(String)

    # Metadata
    genres = Column(ARRAY(String), default=[])
    original_language = Column(String, default="en")
    spoken_languages = Column(ARRAY(String), default=[])
    production_countries = Column(ARRAY(String), default=[])
    production_companies = Column(ARRAY(String), default=[])

    # Technical Details
    runtime = Column(Integer)  # Duration in minutes
    status = Column(String)  # Released, Post Production, etc.
    adult = Column(Boolean, default=False)

    # TMDB Metadata
    tmdb_id = Column(Integer, unique=True)
    imdb_id = Column(String)
    homepage = Column(String)

    # Financial (optional - for analytics)
    budget = Column(BigInteger, default=0)
    revenue = Column(BigInteger, default=0)

    # Ratings
    vote_average = Column(Float, default=0.0)
    vote_count = Column(Integer, default=0)
    popularity = Column(Float, default=0.0)
