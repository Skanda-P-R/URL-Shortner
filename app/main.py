import logging
from contextlib import asynccontextmanager
from typing import Optional
from fastapi import Depends, FastAPI, HTTPException, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import db_session, redis_instance
from app.api.v1.router import api_v1_router
from app.core.config import settings
from app.core.database import engine, init_db
from app.core.redis import close_redis_pool, init_redis_pool
from app.services.url_service import resolve_url

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("url_shortener")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize DB tables & Redis connection pool
    logger.info("Initializing database tables...")
    await init_db()
    logger.info("Initializing Redis connection...")
    await init_redis_pool()
    yield
    # Shutdown: Close Redis connection and DB engine
    logger.info("Shutting down Redis connection...")
    await close_redis_pool()
    logger.info("Disposing DB engine...")
    await engine.dispose()


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="High-performance URL Shortener service with non-sequential Base62 IDs and Redis caching.",
    lifespan=lifespan,
)

# CORS Middleware
origins = (
    [origin.strip() for origin in settings.ALLOWED_ORIGINS.split(",")]
    if isinstance(settings.ALLOWED_ORIGINS, str)
    else settings.ALLOWED_ORIGINS
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins if origins != ["*"] else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API v1
app.include_router(api_v1_router, prefix="/api/v1")


@app.get("/", tags=["Health"])
async def root():
    """Service status and quick links."""
    return {
        "service": settings.PROJECT_NAME,
        "status": "healthy",
        "docs_url": "/docs",
        "version": settings.VERSION,
    }


@app.get("/healthz", tags=["Health"])
async def healthz():
    """Health check probe for container orchestrators (Render, Docker, Kubernetes)."""
    return {"status": "ok"}


@app.api_route(
    "/{short_code}",
    methods=["GET", "HEAD"],
    response_class=RedirectResponse,
    status_code=status.HTTP_307_TEMPORARY_REDIRECT,
    summary="Redirect to original URL",
    description="Resolves short_code via Redis cache (hit) or PostgreSQL (miss) and redirects.",
    tags=["Redirect"],
)
async def redirect_short_url(
    short_code: str,
    response: Response,
    db: AsyncSession = Depends(db_session),
    redis: Optional[Redis] = Depends(redis_instance),
):
    target_url, is_cache_hit = await resolve_url(db=db, redis=redis, short_code=short_code)

    if not target_url:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Short URL '{short_code}' not found.",
        )

    # Return 307 Temporary Redirect with cache debug header
    return RedirectResponse(
        url=target_url,
        status_code=status.HTTP_307_TEMPORARY_REDIRECT,
        headers={"X-Cache": "HIT" if is_cache_hit else "MISS"},
    )
