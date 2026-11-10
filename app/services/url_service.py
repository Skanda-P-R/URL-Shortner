import logging
from typing import Optional, Tuple
from redis.asyncio import Redis
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.base62 import encode_base62, generate_non_sequential_id
from app.core.redis import get_cached_url, set_cached_url
from app.models.url import URLItem

logger = logging.getLogger(__name__)


async def shorten_url(
    db: AsyncSession,
    redis: Optional[Redis],
    original_url: str,
    max_retries: int = 5,
) -> Tuple[URLItem, bool]:
    """
    Shortens a URL or returns the existing record if URL was previously shortened.

    Returns:
        (URLItem, is_new: bool)
    """
    # 1. Deduplication check: Has this exact URL already been shortened?
    stmt = select(URLItem).where(URLItem.original_url == original_url)
    result = await db.execute(stmt)
    existing_item = result.scalar_one_or_none()

    if existing_item:
        # Pre-warm Redis cache so subsequent lookups are immediate hits
        await set_cached_url(redis, existing_item.short_code, existing_item.original_url)
        return existing_item, False

    # 2. Generate non-sequential ID and Base62 short_code with collision retries
    for attempt in range(max_retries):
        unique_id = generate_non_sequential_id()
        short_code = encode_base62(unique_id)

        new_item = URLItem(
            id=unique_id,
            original_url=original_url,
            short_code=short_code,
            click_count=0,
        )

        try:
            db.add(new_item)
            await db.commit()
            await db.refresh(new_item)

            # Pre-warm cache for the new short URL
            await set_cached_url(redis, new_item.short_code, new_item.original_url)
            return new_item, True

        except IntegrityError as exc:
            await db.rollback()
            # If the conflict was on original_url (due to concurrent request), return existing
            concurrent_check = await db.execute(stmt)
            concurrent_item = concurrent_check.scalar_one_or_none()
            if concurrent_item:
                await set_cached_url(
                    redis, concurrent_item.short_code, concurrent_item.original_url
                )
                return concurrent_item, False

            # Otherwise, collision on id or short_code; retry loop
            logger.warning(
                f"Collision on attempt {attempt + 1}/{max_retries} for id={unique_id}. Retrying..."
            )

    raise RuntimeError("Failed to generate unique non-sequential ID after maximum retries.")


async def resolve_url(
    db: AsyncSession,
    redis: Optional[Redis],
    short_code: str,
) -> Tuple[Optional[str], bool]:
    """
    Resolves a short_code to its original target URL using Cache-Aside pattern.

    Returns:
        (target_url: Optional[str], is_cache_hit: bool)
    """
    # 1. Check Redis Cache
    cached_url = await get_cached_url(redis, short_code)
    if cached_url:
        # Cache Hit! Asynchronously bump click count in DB without blocking redirect
        try:
            stmt = (
                update(URLItem)
                .where(URLItem.short_code == short_code)
                .values(click_count=URLItem.click_count + 1)
            )
            await db.execute(stmt)
            await db.commit()
        except Exception as e:
            logger.warning(f"Could not increment click count on cache hit: {e}")
        return cached_url, True

    # 2. Cache Miss: Query PostgreSQL (indexed by short_code)
    stmt = select(URLItem).where(URLItem.short_code == short_code)
    result = await db.execute(stmt)
    item = result.scalar_one_or_none()

    if not item:
        return None, False

    # Cache Miss Hit in DB: Populate Redis cache for future reads
    await set_cached_url(redis, item.short_code, item.original_url)

    # Increment click count
    item.click_count += 1
    await db.commit()

    return item.original_url, False


async def get_url_details(
    db: AsyncSession,
    short_code: str,
) -> Optional[URLItem]:
    """
    Fetches full metadata for a shortened URL.
    """
    stmt = select(URLItem).where(URLItem.short_code == short_code)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()
