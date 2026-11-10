from datetime import datetime
from typing import Optional
from urllib.parse import urlparse
from pydantic import BaseModel, ConfigDict, Field, field_validator


class URLCreate(BaseModel):
    """Schema for shortening a URL."""
    url: str = Field(
        ...,
        description="The target long URL to be shortened",
        examples=["https://github.com/fastapi/fastapi"],
    )

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        clean = v.strip()
        if not clean:
            raise ValueError("URL cannot be empty.")
        if len(clean) > 2048:
            raise ValueError("URL exceeds maximum length of 2048 characters.")

        parsed = urlparse(clean)
        if parsed.scheme not in ("http", "https"):
            raise ValueError("URL must have 'http' or 'https' protocol.")
        if not parsed.netloc:
            raise ValueError("URL must contain a valid domain name.")

        return clean


class URLResponse(BaseModel):
    """Response returned when shortening a URL."""
    id: int
    short_code: str
    short_url: str
    original_url: str
    qr_code_url: Optional[str] = Field(
        None,
        description="Direct URL to fetch the QR code PNG image",
    )
    created_at: datetime
    is_new: bool = Field(
        ...,
        description="True if newly created, False if existing record was reused (deduplication)",
    )

    model_config = ConfigDict(from_attributes=True)


class URLStatsResponse(BaseModel):
    """Response returned for URL analytics/details."""
    id: int
    short_code: str
    short_url: str
    original_url: str
    click_count: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
