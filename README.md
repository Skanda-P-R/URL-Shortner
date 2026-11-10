# High-Performance FastAPI URL Shortener

A production-ready, ultra-fast URL Shortener service built with **FastAPI**, **PostgreSQL**, and **Redis** using **Python 3.13**.

Designed for high throughput, data integrity, and privacy by implementing **non-sequential IDs**, **Base62 encoding**, **URL deduplication**, and **Cache-Aside Redis caching**.

---

## Key Features

- **Non-Sequential Unique IDs**: Generates cryptographically secure, high-entropy 63-bit IDs within PostgreSQL `BIGINT` range, preventing URL scraping and enumeration attacks.
- **Base62 Encoding**: Compact, URL-safe 7–10 character short slugs (`[0-9a-zA-Z]`).
- **URL Deduplication (Idempotency)**: Enforces unique constraint on `original_url`. If a URL is submitted multiple times, the service returns the existing short URL without creating duplicate database rows.
- **High-Performance Reads & Indexing**: Indexed B-Tree lookups on `short_code` and `original_url` for $O(\log N)$ database query speed.
- **Cache-Aside Redis Layer**:
  - `GET /{short_code}` queries Redis first (`url_shortener:code:{short_code}`).
  - **Cache Hit**: Returns an immediate `307 Temporary Redirect` without touching PostgreSQL.
  - **Cache Miss**: Queries indexed PostgreSQL, writes the result to Redis with a configurable TTL, and completes the redirect.
  - **Cache Pre-warming**: Automatically pre-populates Redis upon URL creation.
- **Async & Non-Blocking**: Built using `asyncio`, `asyncpg`, and `redis.asyncio` for high concurrent throughput.
- **Analytics & Metadata**: Tracks redirect click counts and creation timestamps.
- **Python 3.13 Ready**: Uses the latest modern Python features, typing, and async patterns.

---

## Web Frontend (GitHub Pages)

A modern, responsive web application is included in both [`docs/index.html`](file:///g:/Skanda%20Files/Github%20Repos/URL-Shortner/docs/index.html) and [`index.html`](file:///g:/Skanda%20Files/Github%20Repos/URL-Shortner/index.html).

### Features:
- **Instant Shortening:** Direct integration with `https://danspark-url.onrender.com`.
- **Open in New Tab:** Direct button to open the shortened URL in a new browser tab.
- **Click-to-Copy:** One-click copy with visual feedback.
- **Deduplication Indicators:** Visual badges indicating whether a link was newly created or reused.
- **Cold-Start Detection:** Informs users when Render's free tier backend is waking up.
- **Local History:** Saves recent shortened links in browser `localStorage`.

### How to Enable GitHub Pages:
1. In your GitHub repository, go to **Settings** > **Pages**.
2. Under **Build and deployment** > **Source**, choose **Deploy from a branch**.
3. Select branch **`main`** and folder **`/docs`** (or `/ (root)`).
4. Click **Save**.
5. Your website will be live at:
   `https://<your-github-username>.github.io/URL-Shortner/`

---

## Architecture Diagram

```mermaid
flowchart TD
    Client["Client / Browser"]
    FastAPI["FastAPI App (Python 3.13)"]
    Redis[("Redis Cache")]
    Postgres[("PostgreSQL DB")]

    subgraph "Write: POST /api/v1/shorten"
        Client -->|"1. Submit URL"| FastAPI
        FastAPI -->|"2. Check duplicate original_url"| Postgres
        FastAPI -->|"3. If exists, return existing short_url"| Client
        FastAPI -->|"4. If new, generate non-sequential ID & Base62"| FastAPI
        FastAPI -->|"5. Insert (id, original_url, short_code)"| Postgres
        FastAPI -->|"6. Pre-warm Redis (short_code -> url)"| Redis
        FastAPI -->|"7. Return Short URL"| Client
    end

    subgraph "Read: GET /{short_code}"
        Client -->|"1. Visit short URL"| FastAPI
        FastAPI -->|"2. Check cache (url:short_code)"| Redis
        Redis -->|"Cache Hit: Return URL"| FastAPI
        FastAPI -->|"3. Cache Miss: Query short_code"| Postgres
        Postgres -->|"Return record"| FastAPI
        FastAPI -->|"4. Populate Redis (with TTL)"| Redis
        FastAPI -->|"5. 307 Temporary Redirect"| Client
    end
```

---

## Project Structure

```
URL-Shortner/
├── app/
│   ├── api/
│   │   ├── deps.py                  # Database and Redis dependency injection
│   │   └── v1/
│   │       ├── endpoints/
│   │       │   ├── shorten.py       # POST /api/v1/shorten (creation & deduplication)
│   │       │   └── urls.py          # GET /api/v1/urls/{code} (analytics & metadata)
│   │       └── router.py            # API v1 router
│   ├── core/
│   │   ├── base62.py                # Non-sequential ID generator & Base62 encoder/decoder
│   │   ├── config.py                # Pydantic BaseSettings (.env loading)
│   │   ├── database.py              # Async SQLAlchemy engine & session factory
│   │   └── redis.py                 # Async Redis client lifecycle & cache helpers
│   ├── models/
│   │   └── url.py                   # SQLAlchemy URLItem model with unique indices
│   ├── schemas/
│   │   └── url.py                   # Pydantic request/response validation schemas
│   ├── services/
│   │   └── url_service.py           # Core business logic (deduplication & cache-aside)
│   └── main.py                      # FastAPI application & root redirect handler
├── alembic/                         # Database migrations
│   ├── versions/
│   │   └── 001_create_urls_table.py
│   ├── env.py
│   └── script.py.mako
├── tests/                           # Pytest test suite (16 tests)
│   ├── conftest.py                  # In-memory SQLite & fakeredis fixtures
│   ├── test_api.py                  # API integration tests
│   ├── test_base62.py               # Unit tests for Base62 & non-sequential IDs
│   └── test_url_service.py          # Service layer & cache hit/miss tests
├── .env.example                     # Environment template
├── .gitignore
├── alembic.ini
├── Dockerfile                       # Python 3.13 container definition
├── docker-compose.yml               # Multi-container setup (Web + Postgres + Redis)
├── pytest.ini
├── requirements.txt                 # Dependencies
├── DEPLOYMENT_PREREQUISITES.md      # 100% Free deployment guide (Render + Neon + Upstash)
└── README.md
```

---

## Getting Started Locally

### Option A: Running with Docker Compose (Recommended)

Requires Docker Desktop installed.

1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd URL-Shortner
   ```

2. **Start all services** (FastAPI, PostgreSQL 16, Redis 7):
   ```bash
   docker compose up --build
   ```

3. **Access the application**:
   - API Base: `http://localhost:8000`
   - Interactive Swagger Docs: `http://localhost:8000/docs`
   - Health Check: `http://localhost:8000/healthz`

---

### Option B: Running Locally with Python 3.13

1. **Create and activate a Python 3.13 virtual environment**:
   ```powershell
   py -3.13 -m venv venv
   .\venv\Scripts\activate
   ```

2. **Install dependencies**:
   ```powershell
   pip install -r requirements.txt
   ```

3. **Configure Environment Variables**:
   Copy `.env.example` to `.env`:
   ```powershell
   Copy-Item .env.example .env
   ```
   Ensure your `.env` contains valid connection strings:
   ```env
   DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/urlshortener
   REDIS_URL=redis://localhost:6379/0
   BASE_URL=http://localhost:8000
   ```

4. **Run database migrations**:
   ```powershell
   alembic upgrade head
   ```

5. **Start the FastAPI development server**:
   ```powershell
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

---

## API Reference & Examples

### 1. Shorten a URL
- **Endpoint:** `POST /api/v1/shorten`
- **Request:**
  ```bash
  curl -X POST "http://localhost:8000/api/v1/shorten" \
       -H "Content-Type: application/json" \
       -d '{"url": "https://fastapi.tiangolo.com/tutorial/"}'
  ```
- **Response (`201 Created` for new URL):**
  ```json
  {
    "id": 847291048291047,
    "short_code": "k9Za3B",
    "short_url": "http://localhost:8000/k9Za3B",
    "original_url": "https://fastapi.tiangolo.com/tutorial/",
    "created_at": "2026-11-10T10:00:00Z",
    "is_new": true
  }
  ```
- **Deduplication:** If the identical URL is submitted again, it returns `200 OK` with `is_new: false` and the existing short code. No duplicate database rows are created.

---

### 2. Redirect to Original URL
- **Endpoint:** `GET /{short_code}`
- **Request:**
  ```bash
  curl -I "http://localhost:8000/k9Za3B"
  ```
- **Response:**
  ```http
  HTTP/1.1 307 Temporary Redirect
  Location: https://fastapi.tiangolo.com/tutorial/
  X-Cache: HIT
  ```
  *(Returns `X-Cache: HIT` when retrieved from Redis, or `X-Cache: MISS` when loaded from PostgreSQL).*

---

### 3. URL Analytics & Details
- **Endpoint:** `GET /api/v1/urls/{short_code}`
- **Request:**
  ```bash
  curl "http://localhost:8000/api/v1/urls/k9Za3B"
  ```
- **Response (`200 OK`):**
  ```json
  {
    "id": 847291048291047,
    "short_code": "k9Za3B",
    "short_url": "http://localhost:8000/k9Za3B",
    "original_url": "https://fastapi.tiangolo.com/tutorial/",
    "click_count": 42,
    "created_at": "2026-11-10T10:00:00Z",
    "updated_at": "2026-11-10T10:15:30Z"
  }
  ```

---

## Running Automated Tests

The test suite runs against an isolated in-memory SQLite database and `fakeredis`, requiring zero external services to run.

```powershell
pytest -v
```

Output:
```
tests/test_api.py::test_health_endpoints PASSED
tests/test_api.py::test_shorten_and_deduplication_api PASSED
tests/test_api.py::test_redirect_endpoint PASSED
tests/test_api.py::test_redirect_404_for_unknown PASSED
tests/test_api.py::test_url_stats_endpoint PASSED
tests/test_api.py::test_invalid_url_rejection PASSED
tests/test_base62.py::test_encode_decode_zero PASSED
tests/test_base62.py::test_encode_decode_positive_integers PASSED
tests/test_base62.py::test_encode_negative_raises PASSED
tests/test_base62.py::test_decode_invalid_character_raises PASSED
tests/test_base62.py::test_decode_empty_string_raises PASSED
tests/test_base62.py::test_generate_non_sequential_id PASSED
tests/test_url_service.py::test_shorten_url_deduplication PASSED
tests/test_url_service.py::test_resolve_url_cache_hit_and_miss PASSED
tests/test_url_service.py::test_resolve_non_existent_url PASSED
tests/test_url_service.py::test_get_url_details PASSED

============================= 16 passed in 0.35s ==============================
```

---

## Free Cloud Deployment

To deploy this service online for **100% free** using **Neon** (Postgres), **Upstash** (Redis), and **Render** (FastAPI), refer to the step-by-step prerequisite guide:
👉 **[DEPLOYMENT_PREREQUISITES.md](DEPLOYMENT_PREREQUISITES.md)**
