from __future__ import annotations

import os
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from typing import Any

import fastf1
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent


def _cache_dir_from_env() -> Path:
    configured = os.getenv("FASTF1_CACHE_DIR", "").strip()
    if not configured:
        return BASE_DIR / "ff1cache"

    path = Path(configured).expanduser()
    if not path.is_absolute():
        path = BASE_DIR / path
    return path.resolve()


CACHE_DIR = _cache_dir_from_env()
CACHE_DIR.mkdir(parents=True, exist_ok=True)
fastf1.Cache.enable_cache(str(CACHE_DIR))


def _to_int(value: Any, default: int = 0) -> int:
    try:
        if pd.isna(value):
            return default
        return int(value)
    except (TypeError, ValueError):
        return default


def _numeric_series(frame: pd.DataFrame, column: str) -> pd.Series:
    if column not in frame.columns:
        return pd.Series(dtype="float64")
    return pd.to_numeric(frame[column], errors="coerce").dropna()


@lru_cache(maxsize=12)
def get_event_schedule_cached(year: int) -> pd.DataFrame:
    return fastf1.get_event_schedule(year)


def list_supported_years(start_year: int = 2018) -> list[int]:
    """Return seasons the UI may request.

    FastF1 can populate its cache on demand, so the list must not shrink to only
    seasons that happen to have cached data on disk.
    """

    current_year = datetime.now(timezone.utc).year
    if start_year > current_year:
        return []
    return list(range(current_year, start_year - 1, -1))


def list_races_for_year(year: int) -> list[dict[str, Any]]:
    schedule = get_event_schedule_cached(year)
    races: list[dict[str, Any]] = []

    for _, row in schedule.iterrows():
        round_number = _to_int(row.get("RoundNumber"), 0)
        if round_number <= 0:
            continue

        event_date = row.get("EventDate")
        date_iso: str | None = None
        if pd.notna(event_date):
            try:
                date_iso = pd.to_datetime(event_date).date().isoformat()
            except (TypeError, ValueError):
                date_iso = None

        country = str(row.get("Country", "")).strip() or None
        location = str(row.get("Location", "")).strip() or None
        event_name = str(row.get("EventName", f"Round {round_number}")).strip()

        races.append(
            {
                "round": round_number,
                "name": event_name or f"Round {round_number}",
                "country": country,
                "location": location,
                "date": date_iso,
            }
        )

    races.sort(key=lambda race: race["round"])
    return races


@lru_cache(maxsize=4)
def load_race_session(year: int, round_number: int):
    """Load one race session and keep a small in-process hot cache.

    FastF1's own disk cache handles repeat downloads. Telemetry is disabled
    because Overtakr currently needs timing, results, weather and track-status
    data rather than high-frequency car telemetry; this substantially reduces
    cold-start download size and memory usage.
    """

    session = fastf1.get_session(year, round_number, "R")
    session.load(telemetry=False, weather=True, messages=True)
    return session


def extract_safety_car_laps(laps_df: pd.DataFrame) -> list[int]:
    if "TrackStatus" not in laps_df.columns or "LapNumber" not in laps_df.columns:
        return []

    caution_codes = {"4", "5", "6", "7"}
    safety_laps: set[int] = set()

    for _, row in laps_df[["LapNumber", "TrackStatus"]].dropna().iterrows():
        lap = _to_int(row.get("LapNumber"), 0)
        if lap <= 0:
            continue

        status_text = str(row.get("TrackStatus", ""))
        if any(code in status_text for code in caution_codes):
            safety_laps.add(lap)

    return sorted(safety_laps)


def get_weather_summary(session: Any) -> dict[str, float]:
    weather_data = getattr(session, "weather_data", None)
    if weather_data is None or weather_data.empty:
        return {
            "avg_air_temp": 24.0,
            "avg_track_temp": 34.0,
            "rain_probability": 0.0,
            "wind_speed_avg": 8.0,
        }

    air_temp = _numeric_series(weather_data, "AirTemp")
    track_temp = _numeric_series(weather_data, "TrackTemp")
    wind_speed = _numeric_series(weather_data, "WindSpeed")
    rainfall = _numeric_series(weather_data, "Rainfall")

    rain_probability = float((rainfall > 0).mean()) if len(rainfall) else 0.0

    return {
        "avg_air_temp": round(float(air_temp.mean()) if len(air_temp) else 24.0, 1),
        "avg_track_temp": round(float(track_temp.mean()) if len(track_temp) else 34.0, 1),
        "rain_probability": round(rain_probability, 3),
        "wind_speed_avg": round(float(wind_speed.mean()) if len(wind_speed) else 8.0, 1),
    }
