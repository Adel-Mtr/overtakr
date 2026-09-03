# Deployment Guide

Overtakr can be deployed as two services:

- frontend: Next.js (`frontend/`)
- backend: FastAPI (`backend/`)

For a single-machine/self-hosted installation, use `docker compose up --build` from the repository root instead.

## Backend — Render

`render.yaml` is provided at repository root.

1. Create a Render Blueprint from the repository.
2. Set the backend environment variables:
   - `CORS_ALLOW_ORIGINS=https://<frontend-domain>`
   - `FRONTEND_URL=https://<frontend-domain>` (optional)
3. Deploy and copy the backend public URL.
4. Verify `https://<backend-domain>/api/health`.

The FastF1 cache is runtime data. If your hosting filesystem is ephemeral, a restart/redeploy can require race data to be fetched again.

## Backend — Fly.io

The Dockerfile and example configuration are in `backend/`.

Fly app names are globally unique, so replace the `app` value in `backend/fly.toml` (or override it with flyctl) before creating your own deployment.

```bash
cd backend
fly launch --copy-config --ha=false
fly secrets set CORS_ALLOW_ORIGINS=https://<frontend-domain> FRONTEND_URL=https://<frontend-domain>
fly deploy
```

If you want the FastF1 cache to survive machine replacement, attach a Fly volume and mount it at the path configured by `FASTF1_CACHE_DIR`.

## Frontend — Vercel

`frontend/vercel.json` is included.

1. Import the GitHub repository in Vercel.
2. Set **Root Directory** to `frontend`.
3. Set:

```env
NEXT_PUBLIC_API_BASE_URL=https://<backend-domain>
```

4. Deploy.

`NEXT_PUBLIC_API_BASE_URL` is a public browser variable and is embedded during the Next.js build, so changing it requires a new frontend build/deploy.

## Production sanity check

After both services are deployed:

1. `GET /api/health` returns `status: ok`.
2. The frontend loads the season list.
3. Selecting a race loads drivers.
4. A strategy analysis returns leaderboard/chart data.
5. The browser console contains no CORS errors.
6. Refreshing/repeating the same race benefits from FastF1 cache reuse.

## Environment map

### Frontend

- `NEXT_PUBLIC_API_BASE_URL` — public FastAPI origin.

### Backend

- `CORS_ALLOW_ORIGINS` — comma-separated allowed frontend origins.
- `FRONTEND_URL` — optional additional frontend origin.
- `FASTF1_CACHE_DIR` — cache location.
