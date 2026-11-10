# URL Shortener: Free Cloud Deployment Guide & Prerequisites

This step-by-step guide walks you through deploying the URL Shortener service online for **100% free**, with zero credit card required, using modern cloud providers:

| Component | Free Provider | Free Tier Limits |
| :--- | :--- | :--- |
| **PostgreSQL Database** | **[Neon](https://neon.tech)** | 0.5 GB storage, serverless autoscaling, free forever |
| **Redis Cache** | **[Upstash](https://upstash.com)** | 10,000 commands/day, standard Redis URI, free forever |
| **FastAPI Web Service** | **[Render](https://render.com)** | 750 free instance hours/month, automatic HTTPS |

---

## Prerequisites Checklist

Before beginning, ensure you have:
- [x] A **GitHub account** to connect your repository to Render, Neon, and Upstash.
- [x] Git installed locally.
- [x] This repository committed and pushed to your GitHub account.

---

## Step 1: Create a Free PostgreSQL Database on Neon.tech

1. Navigate to **[Neon.tech](https://neon.tech)** and click **Sign Up** (Sign in with your GitHub account).
2. Click **Create Project**:
   - **Project name:** `url-shortener-db`
   - **Postgres version:** `16`
   - **Region:** Choose the region closest to where you will host your app (e.g., `US East (Ohio)` or `EU (Frankfurt)`).
3. Once created, you will see your **Connection details** on the dashboard.
4. Select the **Connection string** tab:
   - Choose **PostgreSQL** in the dropdown.
   - Your connection string will look like this:
     ```
     postgresql://<user>:<password>@ep-cool-cloud-123456.us-east-2.aws.neon.tech/neondb?sslmode=require
     ```
5. **Save this connection string.**
   *(Note: The application automatically transforms `postgresql://` into `postgresql+asyncpg://` behind the scenes, so you can paste the raw connection string directly into your environment variable!)*

---

## Step 2: Create a Free Serverless Redis on Upstash.com

1. Navigate to **[Upstash.com](https://upstash.com)** and click **Get Started** (Sign in with GitHub).
2. Under the **Redis** tab, click **Create Database**:
   - **Name:** `url-shortener-redis`
   - **Type:** Regional
   - **Region:** Select the same region (or closest) as your Neon database.
   - **TLS (SSL):** Enabled (recommended).
   - **Eviction:** Enabled (volatile-lru or allkeys-lru).
3. Click **Create**.
4. In the database dashboard:
   - Scroll down to the **Connect to your database** section.
   - Click the **`redis-py`** or **URI** tab.
   - Copy the connection URL starting with `rediss://`:
     ```
     rediss://default:<password>@cool-dog-12345.upstash.io:6379
     ```
5. **Save this Redis URI.**

---

## Step 3: Push Your Code to GitHub

If you haven't already pushed your code to GitHub:

1. Open PowerShell or Terminal in the project root:
   ```powershell
   git add .
   git commit -m "feat: complete URL shortener with FastAPI, Postgres, Redis"
   ```
2. Create a new repository on [GitHub](https://github.com/new) (e.g., `url-shortener`).
3. Link and push your repository:
   ```powershell
   git remote add origin https://github.com/<your-username>/<your-repo-name>.git
   git branch -M main
   git push -u origin main
   ```

---

## Step 4: Deploy the FastAPI App on Render.com

1. Navigate to **[Render.com](https://render.com)** and sign in using your GitHub account.
2. In the Render Dashboard, click **New +** in the top right and select **Web Service**.
3. Choose **Build and deploy from a Git repository** and connect your `url-shortener` repository.
4. Fill in the service configuration details:
   - **Name:** `my-url-shortener` (or any custom name)
   - **Region:** Same region as Neon / Upstash (e.g., `Oregon (US West)` or `Ohio (US East)`)
   - **Branch:** `main`
   - **Runtime:** `Python 3`
   - **Build Command:**
     ```bash
     pip install -r requirements.txt && alembic upgrade head
     ```
     *(This installs all Python dependencies and automatically creates the `urls` table and indices in Neon).*
   - **Start Command:**
     ```bash
     uvicorn app.main:app --host 0.0.0.0 --port $PORT
     ```
   - **Instance Type:** Select **Free**.

5. Scroll down to the **Environment Variables** section and add the following keys:

| Key | Value | Description |
| :--- | :--- | :--- |
| `DATABASE_URL` | `postgresql://<user>:<pass>@ep-...neon.tech/neondb?sslmode=require` | Your Neon connection string from Step 1 |
| `REDIS_URL` | `rediss://default:<pass>@...upstash.io:6379` | Your Upstash Redis URL from Step 2 |
| `BASE_URL` | `https://my-url-shortener.onrender.com` | Your live Render app URL (shown at the top of your Render dashboard) |
| `CACHE_TTL_SECONDS` | `86400` | Redis cache expiration in seconds (24h) |
| `ALLOWED_ORIGINS` | `*` | CORS origins (set to `*` or your frontend URL) |

6. Click **Create Web Service**.

Render will now pull your repository, install dependencies, run the database migrations, and start the Uvicorn ASGI server!

---

## Step 5: Verify Your Live Deployment

Once the build logs output `Application startup complete`, copy your live URL (e.g., `https://my-url-shortener.onrender.com`):

### 1. Test Swagger Interactive Documentation
Open your browser and visit:
```
https://my-url-shortener.onrender.com/docs
```
You can interactively test the endpoints directly from the browser!

### 2. Test URL Shortening (cURL)
```bash
curl -X POST "https://my-url-shortener.onrender.com/api/v1/shorten" \
     -H "Content-Type: application/json" \
     -d '{"url": "https://news.ycombinator.com"}'
```
Response:
```json
{
  "id": 928374198234,
  "short_code": "k9Za3B",
  "short_url": "https://my-url-shortener.onrender.com/k9Za3B",
  "original_url": "https://news.ycombinator.com",
  "created_at": "2026-11-10T11:00:00Z",
  "is_new": true
}
```

### 3. Test Deduplication
Send the exact same request again:
```bash
curl -X POST "https://my-url-shortener.onrender.com/api/v1/shorten" \
     -H "Content-Type: application/json" \
     -d '{"url": "https://news.ycombinator.com"}'
```
Response:
```json
{
  "id": 928374198234,
  "short_code": "k9Za3B",
  "short_url": "https://my-url-shortener.onrender.com/k9Za3B",
  "original_url": "https://news.ycombinator.com",
  "created_at": "2026-11-10T11:00:00Z",
  "is_new": false
}
```
*(Notice: `is_new: false`, returned the same ID and short code without adding new rows).*

### 4. Test Redirection and Redis Cache Hit
Open the short URL in your browser or run:
```bash
curl -I "https://my-url-shortener.onrender.com/k9Za3B"
```
Header returned:
```http
HTTP/1.1 307 Temporary Redirect
Location: https://news.ycombinator.com
X-Cache: HIT
```

---

## Alternative: Deploying with Docker

If you prefer deploying via container:
1. Render supports **Docker runtime** directly:
   - When creating the Web Service, choose **Docker** instead of Python.
   - Render will build from the repository's `Dockerfile` automatically.
2. In the Render service settings:
   - Set the same environment variables (`DATABASE_URL`, `REDIS_URL`, `BASE_URL`).
   - Run `alembic upgrade head` either as a release command or let the app's `lifespan` auto-initialize tables.

---

## Important Tips for the Free Tier

- **Render Inactivity Spin-Down:** On Render's free tier, services spin down after 15 minutes of zero traffic. The first request after a sleep takes ~30–50 seconds to wake up (cold start). Subsequent requests respond instantly in milliseconds.
- **Neon Serverless Postgres:** Neon databases also scale down to zero when inactive, saving compute. When a query arrives, Neon wakes up within ~500ms.
- **Upstash Redis:** Upstash is serverless and never sleeps, ensuring sub-10ms cache latency at all times.
