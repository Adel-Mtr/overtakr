# Troubleshooting

## The first race load is slow

Overtakr uses FastF1. The first request for a race may need to download and parse timing data. Later requests are cached in `backend/ff1cache/` (or the Docker named volume), so they should be faster.

## The frontend says it cannot reach the API

Confirm the backend is running at `http://localhost:8000` and that `GET /api/health` returns a JSON response. If the API is hosted elsewhere, set `NEXT_PUBLIC_API_BASE_URL` before building the frontend.

## Browser CORS error

Add the exact frontend origin to `CORS_ALLOW_ORIGINS` in `backend/.env`. Multiple origins are comma-separated.

## No races are available

FastF1 needs network access on the first load unless the requested data is already cached. Check the backend logs for the upstream error and retry after connectivity is restored.

## Reset cached race data

Local development:

```bash
rm -rf backend/ff1cache
```

Docker Compose:

```bash
docker compose down -v
```

The cache is generated runtime data and is intentionally not committed to Git.
