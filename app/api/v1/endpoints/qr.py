import base64
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import db_session, redis_instance
from app.core.config import settings
from app.schemas.qr import QRGenerateRequest, QRGenerateResponse
from app.services.qr_service import extract_short_code, get_or_create_qr_code

router = APIRouter()


@router.post(
    "/qr",
    response_model=QRGenerateResponse,
    summary="Generate or retrieve QR code for a short URL",
    description=(
        "Accepts a short URL or short code, checks Redis cache, checks indexed PostgreSQL, "
        "and generates a QR code PNG if not already created. Saved in PostgreSQL (deduplicated) and Redis."
    ),
)
async def generate_qr_code_endpoint(
    payload: QRGenerateRequest,
    db: AsyncSession = Depends(db_session),
    redis: Optional[Redis] = Depends(redis_instance),
) -> QRGenerateResponse:
    short_code = extract_short_code(payload.short_url)
    if not short_code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid short URL or code provided.",
        )

    qr_base64, is_cache_hit = await get_or_create_qr_code(
        db=db,
        redis=redis,
        short_code=short_code,
        base_url=settings.BASE_URL,
    )

    if not qr_base64:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Short URL with code '{short_code}' not found.",
        )

    full_short_url = f"{settings.BASE_URL}/{short_code}"
    qr_image_url = f"{settings.BASE_URL}/api/v1/urls/{short_code}/qr"

    return QRGenerateResponse(
        short_code=short_code,
        short_url=full_short_url,
        qr_image_url=qr_image_url,
        qr_code_base64=qr_base64,
        is_cache_hit=is_cache_hit,
    )


@router.get(
    "/urls/{short_code}/qr",
    summary="Get QR code PNG image directly",
    description="Returns the raw PNG image of the QR code. Supports caching via Redis and database indexing.",
    responses={
        200: {
            "content": {"image/png": {}},
            "description": "Returns raw PNG QR code image.",
        }
    },
)
async def get_qr_image_direct(
    short_code: str,
    download: bool = Query(False, description="Set true to download as attachment file"),
    db: AsyncSession = Depends(db_session),
    redis: Optional[Redis] = Depends(redis_instance),
):
    qr_base64, is_cache_hit = await get_or_create_qr_code(
        db=db,
        redis=redis,
        short_code=short_code,
        base_url=settings.BASE_URL,
    )

    if not qr_base64:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Short URL with code '{short_code}' not found.",
        )

    png_bytes = base64.b64decode(qr_base64)

    headers = {
        "X-Cache": "HIT" if is_cache_hit else "MISS",
        "Cache-Control": f"public, max-age={settings.CACHE_TTL_SECONDS}",
    }

    if download:
        headers["Content-Disposition"] = f'attachment; filename="qr_{short_code}.png"'

    return Response(content=png_bytes, media_type="image/png", headers=headers)
