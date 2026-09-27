# URL Shortener

A URL-shortening API built with FastAPI, SQLModel, PostgreSQL, and Redis. This repository currently contains the Phase 1 core: link persistence, short-code generation, redirect lookup, and soft deletion.

## Phase 1 features

- Create a short link and persist it in PostgreSQL.
- Generate short codes using an atomic Redis counter and Base62 encoding.
- Redirect a short code to its original URL.
- Soft-delete a link by marking it inactive.
- Define SQLModel tables for links, users, and click logs, with Alembic migrations.

Redis is currently used for the counter only. Link lookups are served from PostgreSQL.

## Architecture

```text
HTTP request
    |
FastAPI link router
    |                         |
Link service             Redis INCR counter
    |
PostgreSQL (SQLModel)
```

## API

The routes are defined in `src/link/routes.py` as an `APIRouter`. They need to be included in a FastAPI application by the app entrypoint.

| Method | Route | Description |
| --- | --- | --- |
| `POST` | `/shorten_url/` | Create a short link. Accepts `long_url`, with optional `custom_alias` and `expires_at` fields. |
| `GET` | `/r/{short_code}` | Redirect to the active link's destination. |
| `DELETE` | `/{short_code}` | Soft-delete a link. |

The short URL returned by the create endpoint uses `BASE_URL` and the `/r/{short_code}/` format.

Example create request:

```json
{
  "long_url": "https://example.com/some/page"
}
```

The create endpoint returns the link UUID, short URL, original URL, creation time, and optional expiry time. A missing or inactive short code returns `404` on redirect.

## Requirements

- Python 3.14 or newer
- PostgreSQL
- Redis
- [`uv`](https://docs.astral.sh/uv/)

## Configuration

Create a `.env` file in the repository root. Keep this file local; do not commit credentials.

```dotenv
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/url_shortener
REDIS_URL=redis://localhost:6379/0
BASE_URL=http://localhost:8000
```

`DATABASE_URL` and `REDIS_URL` are required. `BASE_URL` defaults to `http://localhost:8000`.

## Install dependencies and apply migrations

```bash
uv sync
uv run alembic upgrade head
```

The migration command requires PostgreSQL to be available and configured in `.env`.

## Current scope

This is an in-progress project. The current Phase 1 implementation does not yet include Redis lookup caching, custom-alias handling, expiry enforcement, authentication, rate limiting, click analytics, Docker configuration, or tests. Although request and database models include some fields for planned functionality, those features are not active yet. The repository also does not currently include a FastAPI app entrypoint or a command to launch the API.

## Design choices so far

- PostgreSQL stores link records; SQLModel models and Alembic migrations define the schema.
- Redis `INCR` supplies an atomic counter for unique generated codes, which are encoded in Base62.
- Deletion is soft: the record remains in the database and is marked inactive.
- Redis lookup caching and the remaining checklist phases are future work.
