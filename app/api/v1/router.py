from fastapi import APIRouter
from app.api.v1.endpoints import shorten, urls

api_v1_router = APIRouter()
api_v1_router.include_router(shorten.router, tags=["Shorten"])
api_v1_router.include_router(urls.router, tags=["Analytics & Info"])
