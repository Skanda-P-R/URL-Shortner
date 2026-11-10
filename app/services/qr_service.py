import base64
import io
import logging
from typing import Optional, Tuple
from urllib.parse import urlparse
import qrcode
from qrcode.constants import ERROR_CORRECT_M
from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.redis import get_cached_qr, set_cached_qr
from app.models.url import URLItem

logger = logging.getLogger(__name__)


def generate_qr_png_bytes(data: str) -> bytes:
    """
    Generates a high-quality QR code PNG as raw bytes for the provided target URL/data.
    """
    qr = qrcode.QRCode(
        version=None,  # Automatically determine size based on content length
        error_correction=ERROR_CORRECT_M,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return buffer.getvalue()


def generate_qr_base64(data: str) -> str:
    """
    Generates a Base64-encoded string of the QR code PNG.
    """
    png_bytes = generate_qr_png_bytes(data)
    return base64.b64encode(png_bytes).decode("utf-8")


def extract_short_code(input_str: str) -> str:
    """
    Extracts the clean short code from a full URL, path, or raw code string.
    Examples:
      - 'https://danspark-url.onrender.com/4yzypZsOAW2' -> '4yzypZsOAW2'
      - '/4yzypZsOAW2' -> '4yzypZsOAW2'
      - '4yzypZsOAW2' -> '4yzypZsOAW2'
    """
    cleaned = input_str.strip()
    if "/" in cleaned:
        parsed = urlparse(cleaned)
        path = parsed.path.strip("/")
        # If there are sub-paths, take the last segment
        if path:
            return path.split("/")[-1]
    return cleaned


async def get_or_create_qr_code(
    db: AsyncSession,
    redis: Optional[Redis],
    short_code: str,
    base_url: str,
) -> Tuple[Optional[str], bool]:
    """
    Retrieves or generates a QR code for a given short_code.
    
    1. Checks Redis cache.
    2. Checks PostgreSQL (indexed by short_code).
    3. If not present in DB, generates QR code PNG, saves to DB (deduplication) and Redis.

    Returns:
        (qr_base64: Optional[str], is_cache_hit: bool)
    """
    # 1. Check Redis Cache
    cached_qr = await get_cached_qr(redis, short_code)
    if cached_qr:
        return cached_qr, True

    # 2. Check PostgreSQL (indexed by unique short_code)
    stmt = select(URLItem).where(URLItem.short_code == short_code)
    result = await db.execute(stmt)
    item = result.scalar_one_or_none()

    if not item:
        return None, False

    # If QR code was already generated and stored in Postgres
    if item.qr_code:
        await set_cached_qr(redis, short_code, item.qr_code)
        return item.qr_code, False

    # 3. Generate QR code for the short URL
    full_short_url = f"{base_url.rstrip('/')}/{item.short_code}"
    qr_base64 = generate_qr_base64(full_short_url)

    # Persist in PostgreSQL (Deduplication)
    try:
        item.qr_code = qr_base64
        await db.commit()
        await db.refresh(item)
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to save QR code in PostgreSQL for '{short_code}': {e}")

    # Persist in Redis Cache
    await set_cached_qr(redis, short_code, qr_base64)

    return qr_base64, False
