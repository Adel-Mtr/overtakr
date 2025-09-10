from typing import List
from fastapi import FastAPI
from pydantic import BaseModel
from fastf1_utils import get_race_laps
from simulator import simulate_strategy
from fastapi.middleware.cors import CORSMiddleware
from fastf1 import get_event_schedule, get_event

app = FastAPI(title="Overtakr API", version="0.3")


# Allow frontend to call backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class Strategy(BaseModel):
    name: str
    pit_laps: str


class SimulationRequest(BaseModel):
    year: int
    round: int
    strategies: List[Strategy]


@app.post("/api/simulate")
def simulate(req: SimulationRequest):
    laps_df = get_race_laps(req.year, req.round)

    results = {}
    for strat in req.strategies:
        pit_list = [int(x) for x in strat.pit_laps.split(",") if x.isdigit()]
        lap_times = simulate_strategy(laps_df, pit_list)
        results[strat.name] = lap_times

    return {"race": f"{req.year} R{req.round}", "strategies": results}


app = FastAPI(title="Overtakr API", version="0.2")


@app.get("/api/races")
def list_races(year: int):
    """Return all races for a given year"""
    schedule = get_event_schedule(year)
    return [
        {"round": int(row["RoundNumber"]), "name": row["EventName"]}
        for _, row in schedule.iterrows()
    ]


@app.get("/api/drivers")
def list_drivers(year: int, round: int):
    """Return drivers for a given race"""
    event = get_event(year, round)
    session = event.get_session("R")  # Race session
    session.load()
    drivers = session.results["Abbreviation"].tolist()
    return drivers
