# API

FastAPI + PostgreSQL backend for the store. The website still runs on mock data until it is switched over to this API.

## Requirements

- Python 3.12 or newer
- Docker (for the local PostgreSQL database)

## Setup

From the repo root:

```bash
docker compose up -d db          # PostgreSQL on localhost:5432 (creates wearai and wearai_test)
cp .env.example .env             # if you have not already

cd apps/api
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

alembic upgrade head             # create the tables
python -m app.seed               # load the starter catalogue (safe to run again)
uvicorn app.main:app --reload    # http://localhost:8000/docs
```

Check it works: <http://localhost:8000/api/v1/health> returns `{"status": "ok", "database": "ok"}`.

## Endpoints

All under `/api/v1`. JSON uses camelCase, matching the website's types. Interactive docs are at `/docs`.

| Endpoint                       | What it returns                                                                                                                                       |
| ------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------- |
| `GET /health`                  | API and database status                                                                                                                               |
| `GET /products`                | Paginated products. Filters: `gender`, `category`, `size`, `colour` (repeatable), `min`, `max`. Sort: `featured`, `newest`, `price-asc`, `price-desc` |
| `GET /products/{slug}`         | A product with its colourways and rating                                                                                                              |
| `GET /products/{slug}/reviews` | Reviews for the product's style                                                                                                                       |
| `GET /products/{slug}/related` | Other products in the same category (`limit` up to 12)                                                                                                |
| `GET /collections/{slug}`      | A collection: title, filter options and its filtered, sorted products                                                                                 |
| `GET /search?q=`               | Ranked search results                                                                                                                                 |

Pagination uses `page` and `pageSize` (default 24, at most 100). Unknown slugs return 404, and invalid query values return 422 instead of being ignored.

## Authentication

- Passwords are hashed with Argon2id. Only the hash is stored.
- A sign-in sets a random token in an `HttpOnly`, `SameSite=Lax` cookie (`Secure` when `COOKIE_SECURE=true`). The database stores only the token's SHA-256 hash, sessions last 14 days, and logout deletes them.
- Browser POSTs whose `Origin` is not in `CORS_ORIGINS` are rejected with 403.
- Validation errors never echo the submitted values, so passwords do not appear in responses.
- Not covered yet: rate limiting and lockout for repeated failed logins (do this at the hosting layer or with a shared store such as Redis), email verification, and password reset.

Set `COOKIE_SECURE=true` in production, where the site is served over HTTPS.

## Tests and linting

```bash
pytest          # runs against the wearai_test database, built by the migrations
ruff check .
ruff format --check .
```

## Database changes

Change the models in `app/models/`, then generate and review a migration:

```bash
alembic revision --autogenerate -m "describe the change"
alembic upgrade head
```

`tests/test_migrations.py` fails if a model changes without a migration.

## Layout

```
app/
  main.py        app factory, CORS, routers under /api/v1
  config.py      settings from environment variables
  db.py          engine, session and Base
  models/        SQLAlchemy models
  api/           route handlers
  seed.py        loads data/catalogue.json
alembic/         migrations
data/            starter catalogue
tests/
```

Prices are stored as whole LKR integers, never floats.
