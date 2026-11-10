import pytest
from app.services.url_service import get_url_details, resolve_url, shorten_url


@pytest.mark.asyncio
async def test_shorten_url_deduplication(test_db, fake_redis):
    url = "https://example.com/unique-test-page"

    # First shorten attempt
    item1, is_new1 = await shorten_url(test_db, fake_redis, url)
    assert is_new1 is True
    assert item1.original_url == url
    assert item1.short_code is not None

    # Second shorten attempt with identical URL (Deduplication)
    item2, is_new2 = await shorten_url(test_db, fake_redis, url)
    assert is_new2 is False
    assert item2.id == item1.id
    assert item2.short_code == item1.short_code
    assert item2.original_url == item1.original_url


@pytest.mark.asyncio
async def test_resolve_url_cache_hit_and_miss(test_db, fake_redis):
    url = "https://example.com/cache-test"
    item, _ = await shorten_url(test_db, fake_redis, url)

    # Invalidate / clear Redis to force a DB cache miss
    await fake_redis.flushall()

    # 1st resolve: Cache Miss -> Loads from Postgres -> Caches in Redis
    resolved_url, is_cache_hit = await resolve_url(test_db, fake_redis, item.short_code)
    assert resolved_url == url
    assert is_cache_hit is False

    # 2nd resolve: Cache Hit -> Fetched straight from Redis
    resolved_url_2, is_cache_hit_2 = await resolve_url(test_db, fake_redis, item.short_code)
    assert resolved_url_2 == url
    assert is_cache_hit_2 is True


@pytest.mark.asyncio
async def test_resolve_non_existent_url(test_db, fake_redis):
    resolved_url, is_cache_hit = await resolve_url(test_db, fake_redis, "nonexistent99")
    assert resolved_url is None
    assert is_cache_hit is False


@pytest.mark.asyncio
async def test_get_url_details(test_db, fake_redis):
    url = "https://example.com/details-test"
    item, _ = await shorten_url(test_db, fake_redis, url)

    fetched = await get_url_details(test_db, item.short_code)
    assert fetched is not None
    assert fetched.id == item.id
    assert fetched.original_url == url
