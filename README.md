# WEARAI

A clothing store website with an AI shopping assistant. The website comes first; a mobile app will reuse the same API later.

## Structure

```
apps/web   Next.js (App Router), TypeScript, Tailwind CSS
apps/api   FastAPI + PostgreSQL (see apps/api/README.md)
```

The website still runs on typed mock data while the API is being built.

## Requirements

- Node.js 20 or newer
- pnpm 10 or newer

## Getting started

The site reads its catalogue from the API, so three things need to be running. One-time setup first:

```bash
cp .env.example .env

cd apps/api
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cd ../..

pnpm install
```

Then, each time you work on the project, in three terminals (or run the first one once):

```bash
pnpm db        # PostgreSQL in Docker (Docker Desktop must be running)
pnpm dev:api   # the API on http://localhost:8000
pnpm dev       # the website on http://localhost:3000
```

The first time only, create the tables and load the starter products:

```bash
cd apps/api && source .venv/bin/activate
alembic upgrade head && python -m app.seed
```

If pages show **"Something went wrong"**, the API (or the database behind it) is usually not running. In development the error page says so and shows the reason.

If you serve the website from a port other than 3000, add its origin to `CORS_ORIGINS` in `.env` (for example `CORS_ORIGINS=["http://localhost:3000","http://localhost:3001"]`). The API refuses browser requests from origins it does not trust; that is its CSRF protection.

The website proxies `/api/*` to the API (`API_URL`, default `http://localhost:8000`), so the browser only talks to one origin. Pages that show products render on request; building the site does not need the API to be running.

## Scripts

| Command       | What it does                    |
| ------------- | ------------------------------- |
| `pnpm dev`    | Start the web app in dev mode   |
| `pnpm build`  | Production build of the web app |
| `pnpm lint`   | Run ESLint                      |
| `pnpm format` | Format the repo with Prettier   |

## Configuration

The brand name and currency live in `apps/web/src/config/site.ts`. Copy `.env.example` to `.env` for local settings; never commit `.env`.
