# Overtakr Frontend

Next.js application for Overtakr's Formula 1 strategy intelligence experience.

## Run locally

With the backend running on port 8000:

```bash
npm ci
cp .env.example .env.local
npm run dev
```

Open `http://localhost:3000`.

## Environment

```env
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

Set `NEXT_PUBLIC_API_BASE_URL` to the public FastAPI origin before building for production.

## Quality checks

```bash
npm run lint
npm run typecheck
npm run build
```

## Main UX areas

- Strategy Builder
- Race Intelligence (pit windows, weather, safety-car context)
- Strategy Delta Charts
- Driver Digest
- Position-change Intelligence

For whole-project setup, Docker Compose and deployment instructions, see the repository root [`README.md`](../README.md).
