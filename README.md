# Overtakr 🏎️

A modern, stylish Formula 1 race companion app.  
Unique features:
- **Race Strategy Visualizer** → "What if Ferrari pitted 3 laps earlier?"
- **Personalized Driver Digest** → your favorite driver's race story
- **Overtake Map** → replay overtakes corner by corner

## Tech Stack
- Frontend: Next.js 14, TypeScript, Tailwind, shadcn/ui, Framer Motion, Recharts
- Backend: FastAPI, Python, FastF1, Postgres (Supabase), Redis
- Infra: Vercel (frontend), Fly.io/Render (backend), Supabase (DB), Upstash (cache)

## Getting Started
1. `cd frontend && npm install && npm run dev`
2. `cd backend && pip install -r requirements.txt && uvicorn main:app --reload`
3. Add `.env.local` and `.env` files with API keys and DB connection strings.
