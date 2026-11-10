from typing import AsyncGenerator, Optional
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.redis import get_redis


async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency that supplies an async SQLAlchemy database session."""
    async for session in get_db():
        yield session


async def redis_instance() -> Optional[Redis]:
    """Dependency that supplies the Redis client instance."""
    return await get_redis()
