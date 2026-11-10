import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_endpoints(client: AsyncClient):
    resp = await client.get("/")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"

    resp_healthz = await client.get("/healthz")
    assert resp_healthz.status_code == 200
    assert resp_healthz.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_shorten_and_deduplication_api(client: AsyncClient):
    payload = {"url": "https://fastapi.tiangolo.com/tutorial/"}

    # 1. First shorten request (Created: 201)
    res1 = await client.post("/api/v1/shorten", json=payload)
    assert res1.status_code == 201
    data1 = res1.json()
    assert data1["is_new"] is True
    assert "short_code" in data1
    assert data1["original_url"] == payload["url"]

    # 2. Second shorten request with identical URL (Reused: 200)
    res2 = await client.post("/api/v1/shorten", json=payload)
    assert res2.status_code == 200
    data2 = res2.json()
    assert data2["is_new"] is False
    assert data2["id"] == data1["id"]
    assert data2["short_code"] == data1["short_code"]


@pytest.mark.asyncio
async def test_redirect_endpoint(client: AsyncClient):
    target = "https://docs.python.org/3/whatsnew/3.13.html"
    shorten_res = await client.post("/api/v1/shorten", json={"url": target})
    assert shorten_res.status_code == 201
    code = shorten_res.json()["short_code"]

    # Test redirect (follow_redirects=False to verify 307 header)
    redirect_res = await client.get(f"/{code}", follow_redirects=False)
    assert redirect_res.status_code == 307
    assert redirect_res.headers["location"] == target


@pytest.mark.asyncio
async def test_redirect_404_for_unknown(client: AsyncClient):
    res = await client.get("/unknownCode123", follow_redirects=False)
    assert res.status_code == 404


@pytest.mark.asyncio
async def test_url_stats_endpoint(client: AsyncClient):
    target = "https://github.com/astral-sh/uv"
    shorten_res = await client.post("/api/v1/shorten", json={"url": target})
    code = shorten_res.json()["short_code"]

    # Call redirect twice to increment click count
    await client.get(f"/{code}", follow_redirects=False)
    await client.get(f"/{code}", follow_redirects=False)

    # Fetch stats
    stats_res = await client.get(f"/api/v1/urls/{code}")
    assert stats_res.status_code == 200
    data = stats_res.json()
    assert data["short_code"] == code
    assert data["original_url"] == target
    assert data["click_count"] >= 2


@pytest.mark.asyncio
async def test_invalid_url_rejection(client: AsyncClient):
    # Invalid schema (not http/https)
    res = await client.post("/api/v1/shorten", json={"url": "ftp://example.com"})
    assert res.status_code == 422

    # Malformed / empty URL
    res2 = await client.post("/api/v1/shorten", json={"url": "not-a-valid-url"})
    assert res2.status_code == 422
