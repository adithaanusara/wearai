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
python -m app.seed               # add the starter products that are missing (never changes existing ones)
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
- **Repeated failed logins are limited**, the same for every account. An account with 5 failed attempts in 15 minutes (`LOGIN_LOCKOUT_ATTEMPTS`, `LOGIN_LOCKOUT_WINDOW_SECONDS`) cannot sign in, even with the right password, until enough of them age out of that rolling window; a successful sign-in resets it (only _consecutive_ failures since the last success ever count, so one success clears an earlier run of failures without deleting anything). One address gets 20 login attempts per 10 minutes across every account it tries (`LOGIN_IP_RATE_LIMIT_REQUESTS`, `LOGIN_IP_RATE_LIMIT_WINDOW_SECONDS`) and 10 registrations per 10 minutes (`REGISTER_IP_RATE_LIMIT_REQUESTS`, `REGISTER_IP_RATE_LIMIT_WINDOW_SECONDS`). Both send 429 with the same message and a `Retry-After` header either way, so the response never says which of the two limits (if either) was the reason, or whether an email exists. Addresses are told apart by a salted hash (`LOGIN_HASH_SALT`, set it to a long random value in production, separate from `CHAT_HASH_SALT`), never stored raw; behind a proxy, configure the server to pass the real client address on (for example `uvicorn --proxy-headers`).
- Not covered yet: 2FA, email verification, and password reset.

Set `COOKIE_SECURE=true` in production, where the site is served over HTTPS.

## Orders

- **The server decides every price.** A request says which products, sizes and quantities; prices, shipping and the total come from the database. Unknown fields, including `price`, `total` and `shipping`, are rejected with 422.
- Send `expectedTotal` (the total the shopper was shown, in whole LKR) and the API refuses an order whose real total is different: it creates nothing and answers 409 with `{ "code": "price_changed", "total": <current total> }`. It is only compared, never used as a price, and it is optional. A retry of an order that already exists is not affected.
- Each order line stores the product's name, colour, size and unit price at purchase time, so history never changes when the catalogue does.
- Send an `Idempotency-Key` header (8 to 64 letters, digits, `-` or `_`) so a double click or retry returns the original order instead of creating a second one. Reusing a key with different data returns 409 with code `idempotency_conflict`.
- Reading someone else's order returns the same 404 as a missing one, so references cannot be probed.
- Validation matches the website (Sri Lankan mobile numbers, 5-digit postal codes, districts within their province) and only accepts ASCII digits.
- Not covered yet: stock levels, order emails and guest order lookup. Staff manage orders in the admin area (see below).

## Payments (PayHere)

`paymentMethod: "card"` pays through [PayHere](https://www.payhere.lk). `cod` and `bank-transfer` are unaffected and never touch this.

- **Set up:** put `PAYHERE_MERCHANT_ID` and `PAYHERE_MERCHANT_SECRET` in `.env` (never in `.env.example`, which is committed) and leave `PAYHERE_MODE=sandbox` until going live. Also set `SITE_URL` and `API_PUBLIC_URL` to whatever the website and API are actually reachable at (in production, real public URLs; PayHere's notification needs `API_PUBLIC_URL` to be reachable from the internet, so on a machine with no public address, that part cannot be exercised end to end). Leaving the PayHere settings blank disables card payment: placing a card order then answers 422 `payment_method_unavailable`, and the checkout page should offer another method.
- **How it works:** placing a card order creates it as `unpaid` and returns a one-time, server-signed set of fields (`payhere` on the response, only on that one response). The website submits those directly to PayHere's hosted page, so card details never pass through this site. A `hash`, made from the merchant secret and the real total, is what stops the browser from setting its own amount.
- **The order's payment is confirmed by PayHere calling back**, at `POST /payments/payhere/notify`, not by the browser being redirected back. That request is verified by its own signature (same merchant secret, a different formula) before anything changes; a request with a wrong or missing signature updates nothing and still answers 200 (so PayHere does not retry it forever). This route is deliberately not behind the origin check other routes use: PayHere calls it directly, with no browser involved.
- `payment_status` (`unpaid`, `pending`, `paid`, `failed`) is separate from the delivery `status`; a `paid` order does not go back to `pending` or `unpaid` on a later or repeated notification. Every notification is recorded in `payment_events`, alongside the delivery status history in the admin area.
- The order row is locked while a notification is applied, so two notifications for the same order (a genuine possibility: PayHere can call more than once) cannot both apply as a real change; the second is recorded as a replay.
- `GET /orders/{reference}/status` is the one public, unauthenticated route in this API: it exists so a guest checkout, which has no session, can poll for the outcome after being sent back from PayHere. It reveals only the two statuses, nothing else about the order, and the reference is an unguessable, randomly generated token, never a sequential id.
- Not covered yet: refunds, saved cards, subscriptions, and any provider other than PayHere.

## Admin area

Every account has a role: `customer` (the default), `staff` or `admin`. Registering never grants a role.

| Role     | Can do                                         |
| -------- | ---------------------------------------------- |
| customer | shop, place orders, see their own orders       |
| staff    | open the admin area and see the dashboard      |
| admin    | everything above, plus users, roles, audit log |

The role is checked by the API on every request, reading it from the database, so changing someone's role takes effect at once (and signs them out everywhere). The website only hides links; it is not what protects anything. Every `/admin` route carries a `role:staff` or `role:admin` tag, and a test walks the API's own schema to check that each route refuses guests (401), refuses people without the role (403) and refuses requests from untrusted origins.

**The first admin is created from the command line, never from the website.** Whoever can run this already controls the server:

```bash
python -m app.admin_cli create-admin you@example.com --name "Your Name"   # asks for a password
python -m app.admin_cli set-role someone@example.com staff
```

Changes made through the API have guard rails: you cannot change your own role, and the last admin cannot be demoted. (The command line can, because it is the way back in if something goes wrong.)

Every admin change is written to the `audit_log` table in the same transaction as the change. A database trigger refuses to update or delete audit rows, so the record cannot be edited later, even by the application. Secrets (passwords, tokens, keys) are removed before anything is logged. The trigger stops row edits and deletes, not `TRUNCATE` by a database owner, so in production the API should connect with a database role that has no `TRUNCATE`, `DELETE` or `UPDATE` privilege on `audit_log`.

### Order management

Staff and admins can search orders (reference, email or name), filter by status, and move an order along. Only these moves exist: pending to confirmed or cancelled, confirmed to shipped or cancelled, shipped to delivered. Delivered and cancelled are final, and a shipped order cannot be cancelled. A status change never touches lines or prices.

Each change states the status the screen showed (`expectedStatus`). The order row is locked while it is checked, so if two people act at once the second gets 409 `stale_status` instead of silently overwriting the first. Every change is stored in `order_status_history` (from, to, who, when) and in the audit log, in the same transaction.

### Product management

Staff can look at every product (including archived ones); only admins can change them. An admin can edit the name, price, compare-at price and description, and archive or restore a product. **Products are never deleted**, because past orders point at them.

- An archived product disappears from the catalogue, collections, search, related items, the colour options of its style, the chat assistant, and the price and size filters. Its page is a 404 and it cannot be quoted or ordered ("no longer available"). A cart that still holds it is told to remove it. Old orders keep the name and price they were bought at.
- Every edit sends the `updatedAt` it was based on. The product row is locked while it is checked, so if two admins save at once the second gets 409 `stale_product` and the page reloads the newer version. Archive and restore work the same way.
- Prices are whole LKR (0 up to 100,000,000) and a compare-at price must be higher than the price. Unknown fields are rejected. An edit that changes nothing writes nothing. Each real change is audited with the old and new values.
- `python -m app.seed` only adds products that are missing, so it never undoes an edit or brings back an archived product.

### Product images

Admins can add, remove and reorder a product's images (up to 8, never fewer than one). The first is the default and the second shows on hover. Each change follows the same rules as other product edits: admin only, based on the product's version (`updatedAt`, so 409 if it is out of date), and audited.

**Uploads are treated as hostile.** The file's name, content type and extension are ignored. The bytes are decoded with Pillow, and only if they really are a JPEG, PNG or WebP are they drawn again into a new file. That drops metadata (such as GPS position) and anything hidden inside or after the image. Refused: SVG and every other format, animated images, files over 5 MB, images under 200 or over 8,000 pixels on a side, and images over 25 megapixels (checked from the header, before any pixel is decoded). Photos are turned upright and shrunk to 2,000 pixels on the long edge. The stored name is a random 32-character value, so it can neither collide nor reach another folder. An upload whose size is not stated up front, or is far over the limit, is refused from its headers before the body is read.

**Where files live.** `app/storage.py` defines a small storage interface (`save`, `delete`, `url_for`, `name_for`). Two implementations exist, chosen by `IMAGE_STORAGE`:

- `local` (the default): files go to `apps/api/uploads/` (git ignores it, override with `UPLOAD_DIR`) and the API serves them at `/api/v1/media/<name>` with an exact content type, `nosniff`, a locked-down content security policy and a one-year cache (names never change). Only names this store generated are served, so a request cannot reach any other file.
- `cloudinary`: for production, where local disk would not survive a redeploy. Set `IMAGE_STORAGE=cloudinary` and `CLOUDINARY_URL` (from Cloudinary's dashboard, exactly as it shows it: `cloudinary://<api_key>:<api_secret>@<cloud_name>` — a common paste mistake is ending up with `CLOUDINARY_URL=cloudinary://...` as the _value_ too, which is refused with a message saying so). Delivery URLs ask Cloudinary for automatic format and quality (`f_auto,q_auto`), which matters on a plan metered by bandwidth as well as storage. The free tier's monthly credits (roughly 25GB of storage and bandwidth combined) are why the 5 MB-per-image and 8-images-per-product limits above are not loosened. `/api/v1/media` keeps working for any image saved before a switch to Cloudinary, but nothing new is ever written there once it is on.

Writing a third class with the same four methods, returned from `get_storage()`, is all a different provider (S3, for instance) would need; nothing else changes. Deleting an image removes it from storage only after the database change is saved, and a failed upload never leaves anything behind, on either backend. Behind a reverse proxy, also cap the request body size there.

Tests for the Cloudinary backend use a fake `cloudinary.uploader` (no network calls, no account needed) except `tests/test_storage_cloudinary_live.py`, which uploads and deletes one real, tiny test image and only runs with `RUN_LIVE_CLOUDINARY_TESTS=1` and a real `CLOUDINARY_URL`.

Not built yet in the admin area: creating products, sizes and colours, cropping, and per-image alt text (the shop uses the product name).

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
