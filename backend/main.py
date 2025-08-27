from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastf1_utils import get_race_laps
from simulator import simulate_strategy

app = FastAPI(title="Overtakr API", version="0.3")

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # adjust if frontend deployed elsewhere
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Unified simulate endpoint for GET and POST
@app.api_route("/api/simulate", methods=["GET", "POST"])
def simulate(
    year: int = Query(..., description="Season year, e.g., 2024"),
    round: int = Query(..., description="Race round number"),
    pit_laps: str = Query("", description="Comma-separated list of pit laps")
):
    """
    Returns simulated lap times for a race.
    GET: can test in browser
    POST: can call from frontend with axios.post
    """
    laps_df = get_race_laps(year, round)

    # Convert pit_laps query to list of integers
    pit_list = [int(x) for x in pit_laps.split(",") if x.isdigit()]

    results = simulate_strategy(laps_df, pit_list)
    return {"race": f"{year} R{round}", "laps": results}
