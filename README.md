# Overtakr

Overtakr is a portfolio-ready Formula 1 strategy intelligence app.
It combines simulation, driver performance storytelling, and overtake dynamics in a single polished dashboard.

## What it does

- Simulates multiple pit strategies on top of race-specific baseline pace.
- Compares outcomes with lap-by-lap charts, cumulative delta, and strategy leaderboard.
- Surfaces pit-window opportunities with a scoring model.
- Generates a driver digest (grid-to-finish swing, pace consistency, stint narrative).
- Builds overtake intelligence from race position shifts.
- Supports shareable scenario links so visitors can reproduce exact strategy setups.

## Product highlights

- Distinct visual identity with animated sections, custom typography, and responsive layout.
- Strong API contract between FastAPI backend and Next.js frontend.
- Offline-friendly mode: if FastF1 schedule endpoints are unavailable, the app falls back to local cache data.

## Tech stack

- Frontend: Next.js 15, React 19, TypeScript, Tailwind, Framer Motion, Recharts
- Backend: FastAPI, Python, FastF1, Pandas
- Data: FastF1 cache + local race artifacts

## Local setup

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

## Environment variables

### `backend/.env`

```env
CORS_ALLOW_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

### `frontend/.env.local`

```env
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

## API endpoints

- `GET /api/health`
- `GET /api/years`
- `GET /api/races?year=2024`
- `GET /api/drivers?year=2024&round=1`
- `POST /api/simulate`
- `GET /api/driver-digest?year=2024&round=1&driver=VER`
- `GET /api/overtake-map?year=2024&round=1&driver=VER`

## Portfolio demo flow

1. Choose a cached race and add 2-3 strategies.
2. Run analysis and compare the leaderboard + gap chart.
3. Highlight Pit Window Radar and Driver Digest.
4. Copy a scenario link and demonstrate reproducibility.
