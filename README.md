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

```bash
pnpm install
cp .env.example .env
pnpm dev
```

The site runs at http://localhost:3000.

## Scripts

| Command       | What it does                    |
| ------------- | ------------------------------- |
| `pnpm dev`    | Start the web app in dev mode   |
| `pnpm build`  | Production build of the web app |
| `pnpm lint`   | Run ESLint                      |
| `pnpm format` | Format the repo with Prettier   |

## Configuration

The brand name and currency live in `apps/web/src/config/site.ts`. Copy `.env.example` to `.env` for local settings; never commit `.env`.
