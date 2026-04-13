# TGLinktree — Linktree for Telegram

A "Linktree for Telegram" platform built as a Telegram Mini App. Users create personalized profile pages with links, content locks (e.g., "join this channel to unlock"), and analytics.

## Tech Stack

- **FastAPI** (async) — API server
- **PostgreSQL** + **asyncpg** — Database
- **Redis** — Caching & rate limiting
- **SQLAlchemy 2.0** (async) — ORM
- **Alembic** — Migrations
- **python-telegram-bot v20** — Bot
- **Pydantic v2** — Validation

## Quick Start

### 1. Prerequisites

- Python 3.11+
- PostgreSQL 15+
- Redis 7+

**Using Docker (recommended):**

```bash
# Start PostgreSQL
docker run -d --name tglinktree-db \
  -e POSTGRES_DB=tglinktree \
  -e POSTGRES_PASSWORD=postgres \
  -p 5432:5432 \
  postgres:15

# Start Redis
docker run -d --name tglinktree-redis \
  -p 6379:6379 \
  redis:7-alpine
```

### 2. Install Dependencies

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
```

### 3. Configure Environment

```bash
cp .env.example .env
# Edit .env with your values (BOT_TOKEN, WEBAPP_URL, etc.)
```

### 4. Initialize Database

```bash
# Generate migration from models
alembic revision --autogenerate -m "initial"

# Apply migration
alembic upgrade head
```

### 5. Run the App

```bash
uvicorn tglinktree.main:app --host 0.0.0.0 --port 3000 --reload
```

The bot will start polling automatically alongside the API server.

## API Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/profiles` | ✅ | Create profile |
| GET | `/api/profiles/me` | ✅ | Get own profile |
| GET | `/api/profiles/{slug}` | ❌ | Public profile |
| PATCH | `/api/profiles/me` | ✅ | Update profile |
| POST | `/api/profiles/me/links` | ✅ | Add link |
| PATCH | `/api/profiles/me/links/{id}` | ✅ | Edit link |
| DELETE | `/api/profiles/me/links/{id}` | ✅ | Delete link |
| POST | `/api/profiles/me/links/reorder` | ✅ | Reorder links |
| POST | `/api/locks` | ✅ | Create lock |
| POST | `/api/locks/{id}/verify` | ✅ | Verify lock |
| DELETE | `/api/locks/{id}` | ✅ | Delete lock |
| POST | `/api/track` | ❌ | Track event |
| GET | `/api/profiles/me/analytics` | ✅ | Get analytics |
| GET | `/api/payments/plans` | ❌ | List plans |

## Authentication

All authenticated endpoints require the `X-Telegram-Init-Data` header with the raw `initData` string from `window.Telegram.WebApp.initData`.

## Plans

| Feature | Free | Pro | Business |
|---------|------|-----|----------|
| Links | 5 | 50 | 500 |
| Analytics | 7 days | 90 days | 365 days |
| Lock types | channel_join | All | All |
| Custom domain | ❌ | ❌ | ✅ |

## Bot Commands

- `/start [slug]` — Open the Mini App (optionally deep-linking to a profile)
- `/myprofile` — Open your profile editor
- `/help` — Show usage info
