"""Add full-text search for films.

Revision ID: add_fts_index
Revises: abc123def456
Create Date: 2026-08-22

This migration adds:
1. A tsvector column `search_vector` for full-text search
2. A trigger function to automatically update search_vector on INSERT/UPDATE
3. A GIN index for fast full-text search
4. A trigram index for fuzzy title matching
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers
revision = "add_fts_index"
down_revision = "abc123def456"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Enable pg_trgm extension for fuzzy matching
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")

    # Add search_vector column (regular column, not generated)
    op.execute("""
        ALTER TABLE films
        ADD COLUMN IF NOT EXISTS search_vector tsvector
    """)

    # Create function to update search_vector (marked as STABLE)
    op.execute("""
        CREATE OR REPLACE FUNCTION update_film_search_vector()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.search_vector :=
                setweight(to_tsvector('english', COALESCE(NEW.title, '')), 'A') ||
                setweight(to_tsvector('english', COALESCE(NEW.overview, '')), 'B') ||
                setweight(to_tsvector('english', COALESCE(array_to_string(NEW.genres, ' '), '')), 'C');
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql STABLE;
    """)

    # Create trigger to update search_vector on INSERT or UPDATE
    op.execute("""
        DROP TRIGGER IF EXISTS trg_update_film_search_vector ON films;
        CREATE TRIGGER trg_update_film_search_vector
            BEFORE INSERT OR UPDATE OF title, overview, genres
            ON films
            FOR EACH ROW
            EXECUTE FUNCTION update_film_search_vector();
    """)

    # Backfill existing rows
    op.execute("""
        UPDATE films
        SET search_vector = setweight(to_tsvector('english', COALESCE(title, '')), 'A')
            || setweight(to_tsvector('english', COALESCE(overview, '')), 'B')
            || setweight(to_tsvector('english', COALESCE(array_to_string(genres, ' '), '')), 'C')
        WHERE search_vector IS NULL;
    """)

    # Create GIN index for fast full-text search
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_films_search_vector
        ON films USING GIN (search_vector)
    """)

    # Create trigram index for fuzzy title matching
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_films_title_trgm
        ON films USING GIN (title gin_trgm_ops)
    """)

    # Create index for popularity (for fallback sorting)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_films_popularity
        ON films (popularity DESC NULLS LAST)
    """)


def downgrade() -> None:
    # Drop trigger and function
    op.execute("DROP TRIGGER IF EXISTS trg_update_film_search_vector ON films")
    op.execute("DROP FUNCTION IF EXISTS update_film_search_vector()")

    # Drop indexes
    op.execute("DROP INDEX IF EXISTS idx_films_search_vector")
    op.execute("DROP INDEX IF EXISTS idx_films_title_trgm")
    op.execute("DROP INDEX IF EXISTS idx_films_popularity")

    # Drop the search_vector column
    op.execute("ALTER TABLE films DROP COLUMN IF EXISTS search_vector")
