"""Central configuration - loads config.yaml and .env at import time."""
from os import getenv
from pathlib import Path

import yaml
from dotenv import load_dotenv


def _find_project_root(start: Path) -> Path:
    """Walk up from this file until we find the project root (config.yaml marker)."""
    for candidate in [start, *start.parents]:
        if (candidate / "config.yaml").exists():
            return candidate
    # Fallback: assume the standard layout (backend/app/shared/core/config.py -> 4 levels up)
    return start.parents[3]


_PROJECT_ROOT = _find_project_root(Path(__file__).resolve())

# Load .env first (sensitive values override yaml)
load_dotenv(_PROJECT_ROOT / ".env")


def _load_yaml():
    """Load config.yaml from project root."""
    config_path = _PROJECT_ROOT / "config.yaml"
    if config_path.exists():
        with open(config_path, "r") as f:
            return yaml.safe_load(f)
    return {}


_yaml = _load_yaml()

# Database configuration (all from .env)
POSTGRES_USER = getenv("POSTGRES_USER", "")
POSTGRES_PASSWORD = getenv("POSTGRES_PASSWORD", "")
POSTGRES_HOST = getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = getenv("POSTGRES_PORT", "5432")
POSTGRES_DB = getenv("POSTGRES_DB", "")

DATABASE_URL = (
    f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}"
    f"@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
)

# Redis configuration
REDIS_HOST = getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(getenv("REDIS_PORT", "6379"))
REDIS_PASSWORD = getenv("REDIS_PASSWORD", "")

REDIS_URL = (
    f"redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/0"
    if REDIS_PASSWORD
    else f"redis://{REDIS_HOST}:{REDIS_PORT}/0"
)

# Seat hold lock TTL in seconds (10 minutes)
SEAT_HOLD_TTL = 600

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

# LLM (OpenAI) configuration
_llm = _yaml.get("llm", {})
LLM_PROVIDER = _llm.get("provider", "openai")
LLM_MODEL = _llm.get("model", "gpt-4o-mini")
LLM_MAX_TOKENS = _llm.get("max_tokens", 1000)
LLM_TEMPERATURE = _llm.get("temperature", 0.7)
LLM_CONVERSATION_TTL = _llm.get("conversation_ttl", 1800)  # 30 minutes
OPENAI_API_KEY = getenv("OPENAI_API_KEY", "")
