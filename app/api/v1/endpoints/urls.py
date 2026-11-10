from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import db_session
from app.core.config import settings
from app.schemas.url import URLStatsResponse
from app.services.url_service import get_url_details

router = APIRouter()


@router.get(
    "/urls/{short_code}",
    response_model=URLStatsResponse,
    summary="Get URL metadata and stats",
    description="Retrieve details including click count and creation timestamp for a short URL.",
)
async def get_url_stats(
    short_code: str,
    db: AsyncSession = Depends(db_session),
) -> URLStatsResponse:
    item = await get_url_details(db=db, short_code=short_code)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Short URL with code '{short_code}' not found.",
        )

    return URLStatsResponse(
        id=item.id,
        short_code=item.short_code,
        short_url=f"{settings.BASE_URL}/{item.short_code}",
        original_url=item.original_url,
        click_count=item.click_count,
        created_at=item.created_at,
        updated_at=item.updated_at,
    )
