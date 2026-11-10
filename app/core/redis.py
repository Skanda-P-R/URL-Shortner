import logging
from typing import Optional
import redis.asyncio as aioredis
from redis.asyncio import Redis

from app.core.config import settings

logger = logging.getLogger(__name__)

# Global redis connection reference
redis_client: Optional[Redis] = None


async def init_redis_pool() -> Optional[Redis]:
    """
    Initializes the async Redis client connection pool.
    If Redis server is unreachable, falls back to in-memory FakeRedis for local development.
    """
    global redis_client
    try:
        redis_client = aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
            socket_connect_timeout=2,
            socket_timeout=2,
            retry_on_timeout=False,
        )
        # Test connection
        await redis_client.ping()
        logger.info("Connected to Redis server successfully.")
        return redis_client
    except Exception as e:
        logger.warning(
            f"Could not connect to Redis server at {settings.REDIS_URL} ({e})."
        )
        try:
            import fakeredis.aioredis
            redis_client = fakeredis.aioredis.FakeRedis(decode_responses=True)
            logger.info("Initialized local in-memory FakeRedis cache fallback successfully.")
            return redis_client
        except Exception as fallback_err:
            logger.warning(f"FakeRedis fallback unavailable: {fallback_err}. Running without cache.")
            return None


async def close_redis_pool() -> None:
    """
    Closes the Redis connection pool.
    """
    global redis_client
    if redis_client:
        await redis_client.aclose()
        redis_client = None
        logger.info("Closed Redis connection.")


async def get_redis() -> Optional[Redis]:
    """
    FastAPI dependency yielding the Redis client.
    """
    return redis_client


def make_cache_key(short_code: str) -> str:
    """Standardized key prefix for URL cache."""
    return f"url_shortener:code:{short_code}"


async def get_cached_url(client: Optional[Redis], short_code: str) -> Optional[str]:
    """
    Attempts to read original URL from Redis. Returns None if miss or Redis offline.
    """
    if not client:
        return None
    try:
        return await client.get(make_cache_key(short_code))
    except Exception as e:
        logger.warning(f"Redis GET failed for code '{short_code}': {e}")
        return None


async def set_cached_url(
    client: Optional[Redis],
    short_code: str,
    original_url: str,
    ttl_seconds: int = settings.CACHE_TTL_SECONDS,
) -> bool:
    """
    Caches original URL in Redis with expiration TTL.
    """
    if not client:
        return False
    try:
        await client.set(make_cache_key(short_code), original_url, ex=ttl_seconds)
        return True
    except Exception as e:
        logger.warning(f"Redis SET failed for code '{short_code}': {e}")
        return False
