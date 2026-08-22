"""Film API endpoints."""
from typing import Optional, List

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.modules.films.dto import FilmResponse, FilmListResponse, FilmSyncResponse
from app.modules.films.film_service import FilmService
from app.shared.db.database import get_db

router = APIRouter(prefix="/api/v1/films", tags=["films"])


@router.get("", response_model=FilmListResponse)
async def list_films(
    q: Optional[str] = Query(None, description="Search query for film title"),
    genres: Optional[str] = Query(None, description="Comma-separated list of genres to filter by"),
    status: Optional[str] = Query(None, description="Filter by status (e.g., Released, Post Production)"),
    skip: int = Query(0, ge=0, description="Number of films to skip"),
    limit: int = Query(20, ge=1, le=100, description="Max films to return"),
    use_fts: bool = Query(False, description="Use full-text search (faster, better ranking)"),
    db: Session = Depends(get_db),
):
    """
    Get all films with optional search and filters.

    Use `use_fts=true` for better search results with PostgreSQL full-text search.
    """
    service = FilmService(db)

    # If search or filters are provided, use search
    if q or genres or status:
        genre_list = [g.strip() for g in genres.split(",")] if genres else None

        # Use FTS if requested (recommended for search)
        if use_fts:
            films, total = service.search_films_fts(
                query=q,
                genres=genre_list,
                status=status,
                skip=skip,
                limit=limit,
            )
        else:
            films, total = service.search_films(
                query=q,
                genres=genre_list,
                status=status,
                skip=skip,
                limit=limit,
            )
    else:
        films = service.get_films(skip=skip, limit=limit)
        total = service.repository.count()

    return FilmListResponse(
        films=[FilmResponse.model_validate(f) for f in films],
        total=total,
        page=(skip // limit) + 1 if limit > 0 else 1,
        per_page=limit,
    )


@router.get("/{film_id}", response_model=FilmResponse)
async def get_film(
    film_id: int,
    db: Session = Depends(get_db),
):
    """Get a single film by ID."""
    service = FilmService(db)
    film = service.get_film_by_id(film_id)

    if not film:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Film not found")

    return FilmResponse.model_validate(film)


@router.get("/tmdb/{tmdb_id}", response_model=FilmResponse)
async def get_film_by_tmdb(
    tmdb_id: int,
    db: Session = Depends(get_db),
):
    """Get a film by TMDB ID."""
    service = FilmService(db)
    film = service.get_film_by_tmdb_id(tmdb_id)

    if not film:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Film not found")

    return FilmResponse.model_validate(film)


@router.post("/sync", response_model=FilmSyncResponse)
async def sync_films(db: Session = Depends(get_db)):
    """Sync films from TMDB to database."""
    service = FilmService(db)
    results = await service.sync_all()
    return FilmSyncResponse(**results)


@router.post("/sync/popular", response_model=dict)
async def sync_popular(
    pages: int = Query(5, ge=1, le=20),
    db: Session = Depends(get_db),
):
    """Sync popular movies from TMDB."""
    service = FilmService(db)
    created, updated = await service.sync_popular_movies(pages=pages)
    return {"created": created, "updated": updated}


@router.get("/search/", response_model=FilmListResponse)
async def search_tmdb(
    q: str = Query(..., min_length=1, description="Search query"),
    page: int = Query(1, ge=1),
    db: Session = Depends(get_db),
):
    """Search for movies on TMDB."""
    from app.modules.films.tmdb_client import tmdb_client

    results = await tmdb_client.search_movies(query=q, page=page)
    movies = results.get("results", [])
    total_results = results.get("total_results", 0)

    films = [tmdb_client.parse_tmdb_movie(m) for m in movies]

    return FilmListResponse(
        films=films,# type: ignore[arg-type]
        total=total_results,
        page=page,
        per_page=len(films),
    )
