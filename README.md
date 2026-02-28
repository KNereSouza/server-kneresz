# server-kneresz

API server for [kneresz.com](https://kneresz.com) -- a minimalist blogging platform with monospace aesthetics.

## Stack

- **Runtime:** Python 3.14, UV
- **Framework:** FastAPI (async)
- **Database:** PostgreSQL 16, SQLAlchemy 2.0 (asyncpg), Alembic
- **Auth:** GitHub OAuth, JWT (access + refresh tokens)
- **Storage:** Cloudflare R2 (S3-compatible) via boto3
- **Rate limiting:** slowapi

## Project structure

```
app/
  config.py          Settings from environment
  database.py        Async engine and session
  dependencies.py    FastAPI dependency injection (auth, DB)
  main.py            App factory, middleware, routers
  models/            SQLAlchemy models (User, Post, Comment, Media, SlugRedirect)
  schemas/           Pydantic v2 request/response schemas
  services/          Business logic (auth, posts, comments, media, sanitizer)
  routers/           HTTP endpoints (auth, posts, comments, media)
  utils/             Slug generation, R2 client
alembic/             Database migrations
tests/               97 tests (unit, service, router)
```

## Setup

### Prerequisites

- [UV](https://docs.astral.sh/uv/)
- PostgreSQL 16+ (or Docker)
- GitHub OAuth app
- Cloudflare R2 bucket

### Environment

```bash
cp .env.example .env
# Fill in all values
```

| Variable | Description |
|---|---|
| `DATABASE_URL` | PostgreSQL connection string (asyncpg) |
| `ADMIN_GITHUB_ID` | GitHub user ID for the single admin account |
| `GITHUB_CLIENT_ID` | GitHub OAuth app client ID |
| `GITHUB_CLIENT_SECRET` | GitHub OAuth app client secret |
| `JWT_SECRET` | Secret key for signing tokens |
| `R2_ENDPOINT` | R2 S3-compatible endpoint |
| `R2_ACCESS_KEY` | R2 access key |
| `R2_SECRET_KEY` | R2 secret key |
| `R2_BUCKET` | R2 bucket name |
| `R2_PUBLIC_URL` | Public URL prefix for uploaded media |
| `CORS_ORIGINS` | JSON array of allowed origins |

### Local development

```bash
# Start PostgreSQL
docker compose up -d db

# Install dependencies and run migrations
uv sync
uv run alembic upgrade head

# Start dev server
uv run uvicorn app.main:app --reload
```

### Docker

```bash
docker compose up --build
```

## API

All endpoints are prefixed at the root (`/`).

### Auth

| Method | Path | Auth | Description |
|---|---|---|---|
| `GET` | `/auth/github` | -- | Redirect to GitHub OAuth |
| `GET` | `/auth/github/callback` | -- | OAuth callback, returns tokens |
| `POST` | `/auth/refresh` | -- | Exchange refresh token for new access token |
| `GET` | `/auth/me` | User | Current user profile |

### Posts

| Method | Path | Auth | Description |
|---|---|---|---|
| `GET` | `/posts` | -- | List posts (query: `tag`, `status`, `offset`, `limit`) |
| `GET` | `/posts/{slug}` | -- | Get post by slug (301 redirect on old slugs) |
| `POST` | `/posts` | Admin | Create post |
| `PUT` | `/posts/{slug}` | Admin | Update post |
| `DELETE` | `/posts/{slug}` | Admin | Soft delete |
| `POST` | `/posts/{slug}/restore` | Admin | Restore soft-deleted post |
| `DELETE` | `/posts/{slug}/purge` | Admin | Hard delete (requires slug confirmation) |

### Comments

| Method | Path | Auth | Description |
|---|---|---|---|
| `GET` | `/posts/{slug}/comments` | -- | List comments for a post |
| `POST` | `/posts/{slug}/comments` | User | Create comment (rate limited: 8/min) |
| `DELETE` | `/comments/{id}` | Owner/Admin | Soft delete |
| `POST` | `/comments/{id}/restore` | Admin | Restore |
| `DELETE` | `/comments/{id}/purge` | Admin | Hard delete |

### Media

| Method | Path | Auth | Description |
|---|---|---|---|
| `GET` | `/media` | Admin | List uploaded media |
| `POST` | `/media` | Admin | Upload file (images: 10MB, video: 100MB) |
| `DELETE` | `/media/{id}` | Admin | Delete media from R2 and DB |
| `POST` | `/admin/media/gc` | Admin | Garbage collect orphaned media |

### Health

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Returns `{"status": "ok"}` |

## Tests

Tests run against a real PostgreSQL instance (same as development).

```bash
# Install dev dependencies
uv sync --group dev

# Run all 97 tests
uv run pytest -v

# With coverage
uv run pytest --cov=app --cov-report=term-missing
```

## License

[MIT](LICENSE)
