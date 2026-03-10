from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any, Union

import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, validator

from fastf1_utils import (
    extract_safety_car_laps,
    get_weather_summary,
    list_races_for_year,
    list_supported_years,
    load_race_session,
)
from simulator import (
    build_baseline_laps,
    build_leaderboard,
    normalize_strategy,
    recommend_pit_windows,
    simulate_single_strategy,
)


def _cors_origins_from_env() -> list[str]:
    configured = os.getenv(
        "CORS_ALLOW_ORIGINS",
        "http://localhost:3000,http://127.0.0.1:3000",
    )
    origins = [origin.strip() for origin in configured.split(",") if origin.strip()]
    return origins or ["*"]


app = FastAPI(
    title="Overtakr API",
    version="1.0.0",
    description="Formula 1 race strategy, digest, and overtake analytics API.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins_from_env(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class Strategy(BaseModel):
    name: str = Field(..., min_length=1, max_length=40)
    pit_laps: Union[str, list[int]] = Field(default="")
    start_compound: str = Field(default="MEDIUM")
    tyre_profile: str = Field(default="balanced")
    fuel_save: float = Field(default=0.0, ge=-0.8, le=1.5)

    @validator("start_compound")
    def normalize_compound(cls, value: str) -> str:
        compound = value.upper().strip()
        if compound not in {"SOFT", "MEDIUM", "HARD"}:
            raise ValueError("start_compound must be one of SOFT, MEDIUM, HARD")
        return compound

    @validator("tyre_profile")
    def normalize_profile(cls, value: str) -> str:
        profile = value.lower().strip()
        if profile not in {"aggressive", "balanced", "conservative"}:
            raise ValueError("tyre_profile must be aggressive, balanced, or conservative")
        return profile


class SimulationRequest(BaseModel):
    year: int = Field(..., ge=2018, le=2100)
    round: int = Field(..., ge=1, le=40)
    driver: str | None = Field(default=None, max_length=3)
    pit_penalty: float = Field(default=21.5, ge=14.0, le=32.0)
    weather_risk: float = Field(default=0.0, ge=0.0, le=1.0)
    strategies: list[Strategy] = Field(..., min_items=1, max_items=6)


def _to_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _to_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _event_name(session: Any, year: int, round_number: int) -> str:
    event = getattr(session, "event", None)
    if event is None:
        return f"{year} Round {round_number}"

    try:
        name = str(event.get("EventName", "")).strip()
        return name or f"{year} Round {round_number}"
    except Exception:
        return f"{year} Round {round_number}"


def _build_driver_digest(session: Any, selected_driver: str | None) -> dict[str, Any]:
    results = session.results.copy()
    laps_df = session.laps.copy()

    if results.empty:
        raise ValueError("No race results available for this event.")

    if selected_driver:
        selected_driver = selected_driver.upper().strip()
        target_rows = results[results["Abbreviation"] == selected_driver]
        if target_rows.empty:
            raise ValueError(f"Driver '{selected_driver}' is not available for this race.")
    else:
        target_rows = results.sort_values(by="Position", ascending=True).head(1)

    driver_row = target_rows.iloc[0]
    driver = str(driver_row.get("Abbreviation", "")).strip()
    full_name = str(driver_row.get("FullName", driver)).strip()
    team = str(driver_row.get("TeamName", "Unknown")).strip()

    driver_laps = laps_df[laps_df["Driver"] == driver].copy()
    valid_laps = driver_laps[driver_laps["LapTime"].notna()].copy()

    best_lap = None
    if not valid_laps.empty:
        best_idx = valid_laps["LapTime"].idxmin()
        best_row = valid_laps.loc[best_idx]
        best_time = best_row["LapTime"]
        best_lap = {
            "lap": _to_int(best_row.get("LapNumber"), 0),
            "time": round(_to_float(best_time.total_seconds(), 0.0), 3),
        }

    avg_lap = 0.0
    consistency_std = 0.0
    if not valid_laps.empty:
        lap_seconds = valid_laps["LapTime"].apply(lambda v: _to_float(v.total_seconds(), 0.0))
        avg_lap = round(_to_float(lap_seconds.mean(), 0.0), 3)
        consistency_std = round(_to_float(lap_seconds.std(), 0.0), 3)

    stints: list[dict[str, Any]] = []
    if "Stint" in driver_laps.columns and not driver_laps.empty:
        grouped = driver_laps.groupby("Stint", dropna=True)
        for _, stint_df in grouped:
            sorted_stint = stint_df.sort_values(by="LapNumber")
            if sorted_stint.empty:
                continue

            first_row = sorted_stint.iloc[0]
            compound = str(first_row.get("Compound", "UNKNOWN")).upper()
            start_lap = _to_int(sorted_stint["LapNumber"].min(), 0)
            end_lap = _to_int(sorted_stint["LapNumber"].max(), 0)
            stints.append(
                {
                    "compound": compound,
                    "start_lap": start_lap,
                    "end_lap": end_lap,
                    "laps": max(0, end_lap - start_lap + 1),
                }
            )

    grid_position = _to_int(driver_row.get("GridPosition"), 0)
    finish_position = _to_int(driver_row.get("Position"), 0)
    places_gained = grid_position - finish_position if grid_position and finish_position else 0

    if places_gained > 2:
        storyline = f"{driver} executed a strong recovery drive with decisive racecraft."
    elif places_gained < -2:
        storyline = f"{driver} lost track position and spent the race in damage-limitation mode."
    else:
        storyline = f"{driver} delivered a controlled race with stable pace management."

    return {
        "driver": driver,
        "full_name": full_name,
        "team": team,
        "grid_position": grid_position,
        "finish_position": finish_position,
        "places_gained": places_gained,
        "best_lap": best_lap,
        "average_lap": avg_lap,
        "consistency_std": consistency_std,
        "stints": stints,
        "storyline": storyline,
    }


def _build_overtake_map(session: Any, selected_driver: str | None) -> dict[str, Any]:
    laps_df = session.laps.copy()
    results = session.results.copy()

    if laps_df.empty or "Position" not in laps_df.columns:
        return {
            "selected_driver": selected_driver,
            "lap_events": [],
            "driver_swings": [],
            "summary": {"total_position_changes": 0, "most_active_lap": None},
        }

    if selected_driver:
        selected_driver = selected_driver.upper().strip()

    position_rows = laps_df[["Driver", "LapNumber", "Position"]].dropna().copy()
    position_rows["LapNumber"] = pd.to_numeric(position_rows["LapNumber"], errors="coerce")
    position_rows["Position"] = pd.to_numeric(position_rows["Position"], errors="coerce")
    position_rows = position_rows.dropna().astype({"LapNumber": int, "Position": int})

    lap_events: list[dict[str, Any]] = []
    for driver_code, driver_df in position_rows.groupby("Driver"):
        ordered = driver_df.sort_values(by="LapNumber")
        prev_position = None
        for _, row in ordered.iterrows():
            current_position = _to_int(row["Position"], 0)
            lap_number = _to_int(row["LapNumber"], 0)
            if prev_position is not None and lap_number > 0:
                gain = prev_position - current_position
                if gain != 0:
                    if selected_driver and driver_code != selected_driver:
                        prev_position = current_position
                        continue
                    lap_events.append(
                        {
                            "lap": lap_number,
                            "driver": str(driver_code),
                            "from": prev_position,
                            "to": current_position,
                            "gain": gain,
                        }
                    )
            prev_position = current_position

    lap_events.sort(key=lambda event: (event["lap"], -abs(event["gain"])))

    driver_swings: list[dict[str, Any]] = []
    if not results.empty:
        for _, row in results.iterrows():
            code = str(row.get("Abbreviation", "")).strip()
            if not code:
                continue
            if selected_driver and code != selected_driver:
                continue

            grid = _to_int(row.get("GridPosition"), 0)
            finish = _to_int(row.get("Position"), 0)
            net = grid - finish if grid and finish else 0
            driver_swings.append(
                {
                    "driver": code,
                    "grid": grid,
                    "finish": finish,
                    "net": net,
                }
            )

    driver_swings.sort(key=lambda swing: swing["net"], reverse=True)

    active_lap = None
    if lap_events:
        lap_counts = pd.Series([event["lap"] for event in lap_events]).value_counts()
        active_lap = _to_int(lap_counts.index[0], 0)

    return {
        "selected_driver": selected_driver,
        "lap_events": lap_events[:240],
        "driver_swings": driver_swings,
        "summary": {
            "total_position_changes": len(lap_events),
            "most_active_lap": active_lap,
        },
    }


@app.get("/api/health")
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "overtakr-api",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/api/years")
def years() -> dict[str, list[int]]:
    return {"years": list_supported_years()}


@app.get("/api/races")
def races(year: int = Query(..., ge=2018, le=2100)) -> dict[str, Any]:
    try:
        race_list = list_races_for_year(year)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Failed to load race schedule: {exc}") from exc

    return {"year": year, "races": race_list}


@app.get("/api/drivers")
def drivers(
    year: int = Query(..., ge=2018, le=2100),
    round: int = Query(..., ge=1, le=40),
) -> dict[str, Any]:
    try:
        session = load_race_session(year, round)
        results = session.results.copy()
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Failed to load drivers: {exc}") from exc

    if results.empty:
        return {"year": year, "round": round, "drivers": []}

    driver_rows: list[dict[str, Any]] = []
    for _, row in results.sort_values(by="Position", ascending=True).iterrows():
        code = str(row.get("Abbreviation", "")).strip()
        if not code:
            continue
        driver_rows.append(
            {
                "code": code,
                "name": str(row.get("FullName", code)).strip(),
                "team": str(row.get("TeamName", "Unknown")).strip(),
                "number": _to_int(row.get("DriverNumber"), 0),
                "position": _to_int(row.get("Position"), 0),
            }
        )

    return {"year": year, "round": round, "drivers": driver_rows}


@app.post("/api/simulate")
def simulate(request: SimulationRequest) -> dict[str, Any]:
    try:
        session = load_race_session(request.year, request.round)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Failed to load race session: {exc}") from exc

    laps_df = session.laps.copy()
    if laps_df.empty:
        raise HTTPException(status_code=404, detail="No lap data available for this race.")

    baseline_laps, baseline_source = build_baseline_laps(
        laps_df=laps_df,
        driver=request.driver.upper() if request.driver else None,
    )
    if not baseline_laps:
        raise HTTPException(status_code=422, detail="Unable to build baseline lap times.")

    weather_summary = get_weather_summary(session)
    combined_weather_risk = max(
        request.weather_risk,
        min(1.0, weather_summary.get("rain_probability", 0.0) * 0.75),
    )

    safety_car_laps = set(extract_safety_car_laps(laps_df))

    strategy_results: dict[str, dict[str, Any]] = {}
    for strategy_input in request.strategies:
        strategy_spec = normalize_strategy(strategy_input.dict())
        strategy_output = simulate_single_strategy(
            base_laps=baseline_laps,
            strategy=strategy_spec,
            pit_penalty=request.pit_penalty,
            safety_car_laps=safety_car_laps,
            weather_risk=combined_weather_risk,
        )
        strategy_results[strategy_spec.name] = strategy_output

    leaderboard = build_leaderboard(strategy_results)
    pit_windows = recommend_pit_windows(
        base_laps=baseline_laps,
        pit_penalty=request.pit_penalty,
        safety_car_laps=safety_car_laps,
    )

    return {
        "meta": {
            "race": _event_name(session, request.year, request.round),
            "year": request.year,
            "round": request.round,
            "total_laps": len(baseline_laps),
            "baseline_source": baseline_source,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        },
        "race_context": {
            "weather": weather_summary,
            "safety_car_laps": sorted(safety_car_laps),
            "pit_penalty": request.pit_penalty,
            "weather_risk": round(combined_weather_risk, 3),
        },
        "strategies": strategy_results,
        "leaderboard": leaderboard,
        "pit_windows": pit_windows,
    }


@app.get("/api/driver-digest")
def driver_digest(
    year: int = Query(..., ge=2018, le=2100),
    round: int = Query(..., ge=1, le=40),
    driver: str | None = Query(default=None, min_length=3, max_length=3),
) -> dict[str, Any]:
    try:
        session = load_race_session(year, round)
        digest = _build_driver_digest(session, driver)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Failed to build digest: {exc}") from exc

    return {
        "year": year,
        "round": round,
        "race": _event_name(session, year, round),
        "digest": digest,
    }


@app.get("/api/overtake-map")
def overtake_map(
    year: int = Query(..., ge=2018, le=2100),
    round: int = Query(..., ge=1, le=40),
    driver: str | None = Query(default=None, min_length=3, max_length=3),
) -> dict[str, Any]:
    try:
        session = load_race_session(year, round)
        payload = _build_overtake_map(session, driver)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Failed to build overtake map: {exc}") from exc

    return {
        "year": year,
        "round": round,
        "race": _event_name(session, year, round),
        **payload,
    }
