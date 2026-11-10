from pydantic import BaseModel, Field


class QRGenerateRequest(BaseModel):
    """Request payload to generate a QR code from a short URL or code."""
    short_url: str = Field(
        ...,
        description="The short URL or short code to generate a QR code for",
        examples=["https://danspark-url.onrender.com/4yzypZsOAW2", "4yzypZsOAW2"],
    )


class QRGenerateResponse(BaseModel):
    """Response containing the QR code and image links."""
    short_code: str
    short_url: str
    qr_image_url: str
    qr_code_base64: str = Field(
        ...,
        description="Raw Base64 string of the PNG QR code (embeddable as data:image/png;base64,...)",
    )
    is_cache_hit: bool
