# Allow running as: cd backend && uv run python -m app
from app.shared.db.init_db import init_db

if __name__ == "__main__":
    init_db()
