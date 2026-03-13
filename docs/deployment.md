# Deployment Guide

This repo deploys as split apps:

- Frontend: Vercel (`frontend` project)
- Backend: Render or Fly.io (`backend` service)

## 1) Deploy Backend (Render)

`render.yaml` is provided at repo root.

1. Create a new Render Blueprint service from this repo.
2. Render picks `backend` as `rootDir`.
3. Set environment variables:
   - `CORS_ALLOW_ORIGINS=https://<your-vercel-domain>`
   - `FRONTEND_URL=https://<your-vercel-domain>`
4. Deploy and copy backend URL (example: `https://overtakr-api.onrender.com`).

## 2) Deploy Backend (Fly.io)

Fly config is in `backend/fly.toml` and Dockerfile is in `backend/Dockerfile`.

```bash
cd backend
flyctl launch --copy-config --ha=false
flyctl secrets set CORS_ALLOW_ORIGINS=https://<your-vercel-domain> FRONTEND_URL=https://<your-vercel-domain>
flyctl deploy
```

## 3) Deploy Frontend (Vercel)

`frontend/vercel.json` is included.

1. Import the repo in Vercel.
2. Set **Root Directory** to `frontend`.
3. Set env var:
   - `NEXT_PUBLIC_API_BASE_URL=https://<your-backend-domain>`
4. Deploy.

## 4) Production env map

### Frontend (`frontend`)

- `NEXT_PUBLIC_API_BASE_URL`

### Backend (`backend`)

- `CORS_ALLOW_ORIGINS`
- `FRONTEND_URL` (optional, auto-added to CORS)

## 5) Post-deploy sanity checks

- Frontend loads and can list races.
- Strategy simulation returns chart data.
- API health endpoint responds: `/api/health`.
- Browser console has no CORS errors.
