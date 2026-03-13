# Overtakr

Overtakr is a polished Formula 1 strategy intelligence product built for portfolio presentation.
It combines race simulation, driver storytelling, and overtake analytics into one cohesive app.

## Case Study

### Problem
F1 strategy discussion is usually fragmented across timing screens, social clips, and static post-race summaries.
There is no single interactive tool that lets users:

- model pit scenarios quickly,
- compare strategy outcomes visually,
- understand driver race stories,
- and inspect position-change momentum.

### Approach
I built Overtakr as a full-stack analytics experience with three integrated lenses:

1. **Strategy Lab**
Run multi-strategy simulations with adjustable pit windows, tyre profile, pit penalty, and weather risk.

2. **Driver Digest**
Generate per-driver race narratives from lap and result data (grid vs finish, consistency, stint story).

3. **Overtake Intelligence**
Track lap-by-lap position swings and summarize race movement hotspots.

### Architecture

- **Frontend**: Next.js 15 + TypeScript + Recharts + Framer Motion
- **Backend**: FastAPI + Pandas + FastF1
- **Deployment split**:
  - Frontend on Vercel
  - Backend on Render or Fly.io

Data flow:

1. Frontend sends scenario payload (`year`, `round`, race conditions, strategy set).
2. Backend loads race session data (live FastF1 or local offline cache fallback).
3. Backend computes simulation outputs, leaderboard, pit windows, digest, and overtake map.
4. Frontend renders comparative charts and shareable scenario links.

### Engineering Decisions

- **Typed API contracts** across frontend/backend for stable integration.
- **Offline fallback** from local `ff1cache` when live schedule/session APIs fail.
- **Scenario URLs** so portfolio viewers can reproduce exact strategy setups.
- **Production CORS wiring** via environment variables (`CORS_ALLOW_ORIGINS`, `FRONTEND_URL`).

### Impact
Overtakr demonstrates end-to-end product engineering, not just UI work:

- Multi-endpoint analytics backend designed for real race workflows.
- Distinct, branded UX suitable for portfolio demo videos and recruiter walkthroughs.
- Reproducible deployment path with ready-to-use configs for Vercel + Render/Fly.

## Product Features

- Multi-strategy race simulation
- Strategy leaderboard + cumulative gap chart
- Pit-window radar scoring
- Driver digest with race storyline
- Overtake activity timeline
- Shareable scenario links

## Local Development

### 1) Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn main:app --reload --port 8000
```

### 2) Frontend

```bash
cd frontend
npm install
cp .env.example .env.local
npm run dev
```

Open `http://localhost:3000`.

## Environment Variables

### Frontend (`frontend/.env.local`)

```env
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
NEXT_PUBLIC_SITE_URL=http://localhost:3000
```

### Backend (`backend/.env`)

```env
CORS_ALLOW_ORIGINS=http://localhost:3000,http://127.0.0.1:3000,https://your-vercel-domain.vercel.app
FRONTEND_URL=
```

## Deployment

Deployment configs are included:

- Vercel frontend config: `frontend/vercel.json`
- Render backend config: `render.yaml`
- Fly backend config: `backend/fly.toml`
- Container image for backend: `backend/Dockerfile`

See full guide: `docs/deployment.md`.

## API Endpoints

- `GET /api/health`
- `GET /api/years`
- `GET /api/races?year=2024`
- `GET /api/drivers?year=2024&round=1`
- `POST /api/simulate`
- `GET /api/driver-digest?year=2024&round=1&driver=VER`
- `GET /api/overtake-map?year=2024&round=1&driver=VER`
