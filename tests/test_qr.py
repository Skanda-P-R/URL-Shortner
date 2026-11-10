import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.models.url import URLItem
from app.services.qr_service import extract_short_code, generate_qr_png_bytes


def test_generate_qr_png_bytes():
    png_bytes = generate_qr_png_bytes("https://danspark-url.onrender.com/test123")
    assert isinstance(png_bytes, bytes)
    # Check PNG magic bytes
    assert png_bytes.startswith(b"\x89PNG\r\n\x1a\n")


def test_extract_short_code():
    assert extract_short_code("https://danspark-url.onrender.com/4yzypZsOAW2") == "4yzypZsOAW2"
    assert extract_short_code("http://localhost:8000/xyz789") == "xyz789"
    assert extract_short_code("/mycode") == "mycode"
    assert extract_short_code("simpleCode") == "simpleCode"
    assert extract_short_code("https://example.com/prefix/slug123?utm=1") == "slug123"


@pytest.mark.asyncio
async def test_qr_generation_api(client: AsyncClient, test_db):
    # 1. First create a short URL
    target = "https://www.python.org"
    shorten_res = await client.post("/api/v1/shorten", json={"url": target})
    assert shorten_res.status_code == 201
    short_data = shorten_res.json()
    short_code = short_data["short_code"]
    short_url = short_data["short_url"]

    # 2. Request QR code for the short URL (POST /api/v1/qr)
    qr_res1 = await client.post("/api/v1/qr", json={"short_url": short_url})
    assert qr_res1.status_code == 200
    qr_data1 = qr_res1.json()
    assert qr_data1["short_code"] == short_code
    assert qr_data1["is_cache_hit"] is False
    assert len(qr_data1["qr_code_base64"]) > 50
    assert "qr_image_url" in qr_data1

    # Verify saved in PostgreSQL (Deduplication)
    stmt = select(URLItem).where(URLItem.short_code == short_code)
    db_item = (await test_db.execute(stmt)).scalar_one()
    assert db_item.qr_code == qr_data1["qr_code_base64"]

    # 3. Second request for QR code (should hit Redis cache)
    qr_res2 = await client.post("/api/v1/qr", json={"short_url": short_url})
    assert qr_res2.status_code == 200
    qr_data2 = qr_res2.json()
    assert qr_data2["is_cache_hit"] is True
    assert qr_data2["qr_code_base64"] == qr_data1["qr_code_base64"]

    # 4. Direct PNG Image endpoint (GET /api/v1/urls/{code}/qr)
    img_res = await client.get(f"/api/v1/urls/{short_code}/qr")
    assert img_res.status_code == 200
    assert img_res.headers["content-type"] == "image/png"
    assert img_res.content.startswith(b"\x89PNG\r\n\x1a\n")

    # 5. Direct PNG with download parameter
    download_res = await client.get(f"/api/v1/urls/{short_code}/qr?download=true")
    assert download_res.status_code == 200
    assert "attachment;" in download_res.headers.get("content-disposition", "")


@pytest.mark.asyncio
async def test_qr_not_found(client: AsyncClient):
    res = await client.post("/api/v1/qr", json={"short_url": "nonExistentCode99"})
    assert res.status_code == 404

    img_res = await client.get("/api/v1/urls/nonExistentCode99/qr")
    assert img_res.status_code == 404
