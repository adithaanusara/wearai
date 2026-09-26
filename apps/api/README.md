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

| Endpoint                       | What it returns                                                                                                                                                                                                                 |
| ------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `GET /health`                  | API and database status                                                                                                                                                                                                         |
| `GET /products`                | Paginated products. Filters: `gender`, `category`, `size`, `colour` (repeatable), `min`, `max`. Sort: `featured`, `newest`, `price-asc`, `price-desc`. `id` (repeatable, up to 50) looks up specific products, as the cart does |
| `GET /products/{slug}`         | A product with its colourways and rating                                                                                                                                                                                        |
| `GET /products/{slug}/reviews` | Reviews for the product's style                                                                                                                                                                                                 |
| `GET /products/{slug}/related` | Other products in the same category (`limit` up to 12)                                                                                                                                                                          |
| `GET /collections/{slug}`      | A collection: title, filter options and its filtered, sorted products                                                                                                                                                           |
| `GET /search?q=`               | Ranked search results                                                                                                                                                                                                           |

Pagination uses `page` and `pageSize` (default 24, at most 100). Unknown slugs return 404, and invalid query values return 422 instead of being ignored.

## Authentication

- Passwords are hashed with Argon2id. Only the hash is stored.
- A sign-in sets a random token in an `HttpOnly`, `SameSite=Lax` cookie (`Secure` when `COOKIE_SECURE=true`). The database stores only the token's SHA-256 hash, sessions last 14 days, and logout deletes them.
- Browser POSTs whose `Origin` is not in `CORS_ORIGINS` are rejected with 403.
- Validation errors never echo the submitted values, so passwords do not appear in responses.
- Not covered yet: rate limiting and lockout for repeated failed logins (do this at the hosting layer or with a shared store such as Redis), email verification, and password reset.

Set `COOKIE_SECURE=true` in production, where the site is served over HTTPS.

## Orders

- **The server decides every price.** A request says which products, sizes and quantities; prices, shipping and the total come from the database. Unknown fields, including `price`, `total` and `shipping`, are rejected with 422.
- Send `expectedTotal` (the total the shopper was shown, in whole LKR) and the API refuses an order whose real total is different: it creates nothing and answers 409 with `{ "code": "price_changed", "total": <current total> }`. It is only compared, never used as a price, and it is optional. A retry of an order that already exists is not affected.
- Each order line stores the product's name, colour, size and unit price at purchase time, so history never changes when the catalogue does.
- Send an `Idempotency-Key` header (8 to 64 letters, digits, `-` or `_`) so a double click or retry returns the original order instead of creating a second one. Reusing a key with different data returns 409 with code `idempotency_conflict`.
- Reading someone else's order returns the same 404 as a missing one, so references cannot be probed.
- Validation matches the website (Sri Lankan mobile numbers, 5-digit postal codes, districts within their province) and only accepts ASCII digits.
- Not covered yet: stock levels, payment processing, order emails, admin status changes and guest order lookup.

## Chat assistant

`POST /chat` takes `{ "messages": [{ "role": "user" | "assistant", "text": "..." }] }` and returns `{ "reply": { "text": "...", "productIds": [...] } }`.

- The Anthropic API key is read from `ANTHROPIC_API_KEY` on the server and never reaches a browser. Put it in `.env`, which git ignores, and never in `.env.example`, which is committed. The Anthropic account also needs credits (Plans & Billing in the Anthropic console); with none, every request fails and the log says the credit balance is too low. With no key, or `CHAT_ENABLED=false`, the endpoint answers 503 and the website shows that the assistant is unavailable.
- The assistant has three read-only tools: search products, get one product, and store information (delivery, payment, sizing, returns, contact). It has no tools for orders or accounts, so it cannot see or change personal data, even if a message tries to trick it.
- Product cards only ever show products that a tool returned in that conversation. An id the model invents is dropped.
- The store does not track stock, so the assistant says which sizes are offered and never claims something is in stock.
- Limits: 20 messages of up to 1,000 characters (6,000 in total) per conversation, at most 5 tool rounds per question, and `CHAT_RATE_LIMIT_REQUESTS` messages per visitor per `CHAT_RATE_LIMIT_WINDOW_SECONDS` (default 20 per 10 minutes). Visitors are told apart by a salted hash of their address (or by account when signed in), and a store-wide `CHAT_DAILY_TOKEN_CAP` stops the assistant for the day. All counts live in the `chat_usage` table, which never stores message text. Set `CHAT_HASH_SALT` to a long random value in production, and run behind a proxy that passes the real client address on.
- The model is `CHAT_MODEL` (default `claude-opus-5`, with adaptive thinking at low effort and Anthropic's server-side refusal fallback). For Haiku 4.5, also set `CHAT_ADAPTIVE_THINKING=false`, `CHAT_EFFORT=none` and `CHAT_REFUSAL_FALLBACKS=false`.
- Tests use a scripted fake model, so they cost nothing. `tests/test_chat_live.py` calls the real API (a few cents) and only runs with `RUN_LIVE_CHAT_TESTS=1` and a key.
- Returns terms and contact details in `app/store_info.py` are placeholders, like on the website. Replace them before launch.

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
