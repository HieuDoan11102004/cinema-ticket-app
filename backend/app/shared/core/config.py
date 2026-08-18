"""Central configuration - loads config.yaml and .env at import time."""
from os import getenv
from pathlib import Path

import yaml
from dotenv import load_dotenv

# Load .env first (sensitive values override yaml)
_env_path = Path(__file__).resolve().parents[3] / ".env"
load_dotenv(_env_path)


def _load_yaml():
    """Load config.yaml from project root."""
    config_path = Path(__file__).resolve().parents[3] / "config.yaml"
    if config_path.exists():
        with open(config_path, "r") as f:
            return yaml.safe_load(f)
    return {}


_yaml = _load_yaml()

# Database configuration (yaml + .env override for sensitive)
_db = _yaml.get("database", {})
POSTGRES_USER = _db.get("user", "")
POSTGRES_PASSWORD = getenv("POSTGRES_PASSWORD", "")
POSTGRES_HOST = _db.get("host", "localhost")
POSTGRES_PORT = str(_db.get("port", "5432"))
POSTGRES_DB = _db.get("db", "")

DATABASE_URL = (
    f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}"
    f"@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
)

# JWT configuration
_jwt = _yaml.get("jwt", {})
JWT_SECRET = getenv("JWT_SECRET", "")
ALGORITHM = _jwt.get("algorithm", "HS256")


def _parse_duration(duration_str: str) -> int:
    """Parse duration string like '30m' or '168h' to minutes (int)."""
    if not duration_str:
        return 30  # default 30 minutes
    if duration_str.endswith("m"):
        return int(duration_str[:-1])
    if duration_str.endswith("h"):
        return int(duration_str[:-1]) * 60
    if duration_str.endswith("s"):
        return int(duration_str[:-1]) // 60
    return int(duration_str)  # assume raw minutes


JWT_ACCESS_TOKEN_EXPIRE = _parse_duration(_jwt.get("JWT_ACCESS_TOKEN_EXPIRE", "30m"))
JWT_REFRESH_TOKEN_EXPIRE = _parse_duration(_jwt.get("JWT_REFRESH_TOKEN_EXPIRE", "168h"))
