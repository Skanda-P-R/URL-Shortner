from typing import Optional
from fastapi import APIRouter, Depends, Response, status
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import db_session, redis_instance
from app.core.config import settings
from app.schemas.url import URLCreate, URLResponse
from app.services.url_service import shorten_url

router = APIRouter()


@router.post(
    "/shorten",
    response_model=URLResponse,
    summary="Shorten a URL",
    description=(
        "Generates a unique non-sequential ID and Base62 short URL. "
        "If the same URL was already shortened, returns the existing record without duplicates."
    ),
)
async def create_short_url(
    payload: URLCreate,
    response: Response,
    db: AsyncSession = Depends(db_session),
    redis: Optional[Redis] = Depends(redis_instance),
) -> URLResponse:
    item, is_new = await shorten_url(db=db, redis=redis, original_url=payload.url)

    if is_new:
        response.status_code = status.HTTP_201_CREATED
    else:
        response.status_code = status.HTTP_200_OK

    return URLResponse(
        id=item.id,
        short_code=item.short_code,
        short_url=f"{settings.BASE_URL}/{item.short_code}",
        original_url=item.original_url,
        qr_code_url=f"{settings.BASE_URL}/api/v1/urls/{item.short_code}/qr",
        created_at=item.created_at,
        is_new=is_new,
    )
