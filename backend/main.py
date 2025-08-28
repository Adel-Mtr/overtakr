# backend/main.py
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastf1_utils import get_race_laps
from simulator import simulate_strategy

# Create app
app = FastAPI(title="Overtakr API", version="0.2")

# CORS (so frontend can talk to backend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # for dev, allow everything
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
@app.get("/api/simulate")
def simulate(
    year: int = Query(..., description="Season year, e.g., 2024"),
    round: int = Query(..., description="Race round number"),
    pit_laps: str = Query("", description="Comma-separated list of pit laps")
    
):
    """
    Returns simulated lap times for a race.
    """
    laps_df = get_race_laps(year, round)

    # Convert "20,35" -> [20, 35]
    pit_list = [int(x) for x in pit_laps.split(",") if x.isdigit()]

    results = simulate_strategy(laps_df, pit_list)

    print("Simulation results:", results[:10])  # log first 10 laps
    return {"race": f"{year} R{round}", "laps": results}
