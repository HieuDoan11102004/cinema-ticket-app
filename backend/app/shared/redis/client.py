"""Redis client for the application."""
import redis.asyncio as redis
from typing import Optional

from app.shared.core.config import REDIS_URL


class RedisClient:
    """Async Redis client wrapper with connection pooling."""

    _instance: Optional["RedisClient"] = None
    _pool: Optional[redis.ConnectionPool] = None
    _client: Optional[redis.Redis] = None

    def __new__(cls) -> "RedisClient":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    async def connect(self) -> None:
        """Initialize the Redis connection pool."""
        if self._pool is None:
            self._pool = redis.ConnectionPool.from_url(
                REDIS_URL,
                decode_responses=True,
                max_connections=20,
            )
            self._client = redis.Redis(connection_pool=self._pool)

    async def disconnect(self) -> None:
        """Close the Redis connection pool."""
        if self._client:
            await self._client.aclose()
            self._client = None
        if self._pool:
            await self._pool.disconnect()
            self._pool = None

    @property
    def client(self) -> redis.Redis:
        """Get the Redis client instance."""
        if self._client is None:
            raise RuntimeError("Redis not connected. Call connect() first.")
        return self._client

    async def health_check(self) -> bool:
        """Check if Redis is reachable."""
        try:
            await self._client.ping()
            return True
        except Exception:
            return False


# Global instance
redis_client = RedisClient()


async def get_redis() -> redis.Redis:
    """Dependency for FastAPI routes to get Redis client."""
    return redis_client.client
