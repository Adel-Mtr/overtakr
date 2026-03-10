from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from typing import Any
import pickle
import re

import fastf1
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
CACHE_DIR = BASE_DIR / "ff1cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)
fastf1.Cache.enable_cache(str(CACHE_DIR))

_SCHEDULE_UNAVAILABLE_YEARS: set[int] = set()
_LIVE_SESSION_UNAVAILABLE_YEARS: set[int] = set()


@dataclass
class OfflineSession:
    event: dict[str, Any]
    laps: pd.DataFrame
    results: pd.DataFrame
    weather_data: pd.DataFrame


def _to_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _clean_text(value: Any, fallback: str = "") -> str:
    text = str(value or "").strip()
    return text or fallback


def _load_cache_payload(file_path: Path) -> Any:
    with file_path.open("rb") as file_handle:
        payload = pickle.load(file_handle)

    if isinstance(payload, dict) and "data" in payload:
        return payload["data"]
    return payload


def _parse_date_from_name(name: str) -> str | None:
    candidate = name.split("_", 1)[0]
    try:
        return datetime.strptime(candidate, "%Y-%m-%d").date().isoformat()
    except ValueError:
        return None


def _fallback_event_name(folder_name: str) -> str:
    if "_" in folder_name:
        _, event_slug = folder_name.split("_", 1)
    else:
        event_slug = folder_name
    return event_slug.replace("_", " ").strip()


def _find_race_session_dir(race_dir: Path) -> Path | None:
    session_dirs = sorted(path for path in race_dir.iterdir() if path.is_dir() and path.name.endswith("_Race"))
    if session_dirs:
        return session_dirs[0]
    return None


def _extract_cached_race_details(race_dir: Path, round_number: int) -> dict[str, Any]:
    session_dir = _find_race_session_dir(race_dir)

    base_record: dict[str, Any] = {
        "round": round_number,
        "name": _fallback_event_name(race_dir.name),
        "country": None,
        "location": None,
        "date": _parse_date_from_name(race_dir.name),
        "__session_dir": str(session_dir) if session_dir else None,
    }

    if session_dir is None:
        return base_record

    session_info_file = session_dir / "session_info.ff1pkl"
    if not session_info_file.exists():
        return base_record

    try:
        info_data = _load_cache_payload(session_info_file)
        meeting = info_data.get("Meeting", {}) if isinstance(info_data, dict) else {}

        country_obj = meeting.get("Country", {}) if isinstance(meeting, dict) else {}
        country_name = country_obj.get("Name") if isinstance(country_obj, dict) else None

        base_record["name"] = _clean_text(meeting.get("Name"), base_record["name"])
        base_record["country"] = _clean_text(country_name) or None
        base_record["location"] = _clean_text(meeting.get("Location")) or None
    except Exception:
        return base_record

    return base_record


def _list_cached_races_with_paths(year: int) -> list[dict[str, Any]]:
    year_dir = CACHE_DIR / str(year)
    if not year_dir.exists() or not year_dir.is_dir():
        return []

    race_dirs = sorted(path for path in year_dir.iterdir() if path.is_dir())
    races: list[dict[str, Any]] = []

    for index, race_dir in enumerate(race_dirs, start=1):
        races.append(_extract_cached_race_details(race_dir, index))

    return races


def _public_race_record(record: dict[str, Any]) -> dict[str, Any]:
    return {
        "round": _to_int(record.get("round"), 0),
        "name": _clean_text(record.get("name"), "Unknown Race"),
        "country": record.get("country"),
        "location": record.get("location"),
        "date": record.get("date"),
    }


def _build_weather_df(session_dir: Path) -> pd.DataFrame:
    weather_file = session_dir / "weather_data.ff1pkl"
    if not weather_file.exists():
        return pd.DataFrame()

    weather_data = _load_cache_payload(weather_file)
    if isinstance(weather_data, pd.DataFrame):
        weather_df = weather_data.copy()
    elif isinstance(weather_data, dict):
        weather_df = pd.DataFrame(weather_data)
    else:
        weather_df = pd.DataFrame()

    if "Time" in weather_df.columns:
        weather_df["Time"] = pd.to_timedelta(weather_df["Time"], errors="coerce")

    return weather_df


def _build_track_status_by_lap(session_dir: Path, lap_df: pd.DataFrame) -> dict[int, str]:
    track_status_file = session_dir / "track_status_data.ff1pkl"
    if not track_status_file.exists() or lap_df.empty or "Time" not in lap_df.columns:
        return {}

    track_data = _load_cache_payload(track_status_file)
    if not isinstance(track_data, dict):
        return {}

    track_df = pd.DataFrame(track_data)
    if track_df.empty or "Time" not in track_df.columns or "Status" not in track_df.columns:
        return {}

    track_df["Time"] = pd.to_timedelta(track_df["Time"], errors="coerce")
    track_df["Status"] = track_df["Status"].astype(str)
    track_df = track_df.dropna(subset=["Time"]).sort_values(by="Time")

    lap_reference = (
        lap_df.dropna(subset=["LapNumber", "Time"])
        .groupby("LapNumber", as_index=False)["Time"]
        .min()
        .sort_values(by="Time")
    )

    if lap_reference.empty or track_df.empty:
        return {}

    merged = pd.merge_asof(
        lap_reference,
        track_df[["Time", "Status"]],
        on="Time",
        direction="backward",
    )

    merged["LapNumber"] = pd.to_numeric(merged["LapNumber"], errors="coerce").astype("Int64")
    merged = merged.dropna(subset=["LapNumber"])
    return {int(row["LapNumber"]): str(row["Status"]) for _, row in merged.iterrows()}


def _build_offline_session(year: int, round_number: int, cached_race: dict[str, Any]) -> OfflineSession:
    session_dir_raw = cached_race.get("__session_dir")
    if not session_dir_raw:
        raise ValueError(f"Offline cache is incomplete for {year} round {round_number}.")

    session_dir = Path(session_dir_raw)
    if not session_dir.exists():
        raise ValueError(f"Offline cache path does not exist: {session_dir}")

    driver_info_payload = _load_cache_payload(session_dir / "driver_info.ff1pkl")
    extended_timing_payload = _load_cache_payload(session_dir / "_extended_timing_data.ff1pkl")
    timing_app_payload = _load_cache_payload(session_dir / "timing_app_data.ff1pkl")

    driver_info: dict[str, dict[str, Any]] = (
        dict(driver_info_payload) if isinstance(driver_info_payload, dict) else {}
    )

    if not isinstance(extended_timing_payload, tuple) or len(extended_timing_payload) < 2:
        raise ValueError("Offline cache is missing extended timing data.")

    lap_df_raw = extended_timing_payload[0]
    position_df_raw = extended_timing_payload[1]

    if not isinstance(lap_df_raw, pd.DataFrame) or lap_df_raw.empty:
        raise ValueError("Offline cache has no lap timing dataframe.")

    lap_df = lap_df_raw.copy()
    lap_df["DriverNumber"] = lap_df["Driver"].astype(str)
    lap_df["LapNumber"] = pd.to_numeric(lap_df.get("NumberOfLaps"), errors="coerce")
    lap_df["LapNumber"] = lap_df["LapNumber"].astype("Int64")
    lap_df = lap_df.dropna(subset=["LapNumber"])
    lap_df["LapNumber"] = lap_df["LapNumber"].astype(int)
    lap_df = lap_df[lap_df["LapNumber"] > 0]

    if "Time" in lap_df.columns:
        lap_df["Time"] = pd.to_timedelta(lap_df["Time"], errors="coerce")
    else:
        lap_df["Time"] = pd.NaT

    if "LapTime" in lap_df.columns:
        lap_df["LapTime"] = pd.to_timedelta(lap_df["LapTime"], errors="coerce")
    else:
        lap_df["LapTime"] = pd.NaT

    number_to_tla: dict[str, str] = {}
    number_to_name: dict[str, str] = {}
    number_to_team: dict[str, str] = {}

    for key, info in driver_info.items():
        if not isinstance(info, dict):
            continue
        number = _clean_text(info.get("RacingNumber"), _clean_text(key))
        tla = _clean_text(info.get("Tla"), number)
        name = _clean_text(info.get("FullName"), tla)
        team = _clean_text(info.get("TeamName"), "Unknown")

        number_to_tla[number] = tla
        number_to_name[number] = name
        number_to_team[number] = team

    lap_df["Driver"] = lap_df["DriverNumber"].map(number_to_tla).fillna(lap_df["DriverNumber"])

    if isinstance(timing_app_payload, pd.DataFrame) and not timing_app_payload.empty:
        app_df = timing_app_payload.copy()
        app_df["DriverNumber"] = app_df["Driver"].astype(str)
        app_df["LapNumber"] = pd.to_numeric(app_df.get("LapNumber"), errors="coerce")
        app_df = app_df.dropna(subset=["LapNumber"])
        app_df["LapNumber"] = app_df["LapNumber"].astype(int)

        if "Time" in app_df.columns:
            app_df["Time"] = pd.to_timedelta(app_df["Time"], errors="coerce")
            app_df = app_df.sort_values(by=["DriverNumber", "LapNumber", "Time"])
        else:
            app_df = app_df.sort_values(by=["DriverNumber", "LapNumber"])

        extra_cols = [col for col in ["Compound", "Stint"] if col in app_df.columns]
        if extra_cols:
            app_df = app_df.drop_duplicates(subset=["DriverNumber", "LapNumber"], keep="last")
            lap_df = lap_df.merge(
                app_df[["DriverNumber", "LapNumber", *extra_cols]],
                on=["DriverNumber", "LapNumber"],
                how="left",
                suffixes=("", "_app"),
            )

            if "Compound_app" in lap_df.columns:
                base_compound = lap_df["Compound"] if "Compound" in lap_df.columns else pd.Series(index=lap_df.index)
                lap_df["Compound"] = lap_df["Compound_app"].where(lap_df["Compound_app"].notna(), base_compound)
                lap_df = lap_df.drop(columns=["Compound_app"])

            if "Stint_app" in lap_df.columns:
                base_stint = lap_df["Stint"] if "Stint" in lap_df.columns else pd.Series(index=lap_df.index)
                lap_df["Stint"] = lap_df["Stint_app"].where(lap_df["Stint_app"].notna(), base_stint)
                lap_df = lap_df.drop(columns=["Stint_app"])

    if "Compound" not in lap_df.columns:
        lap_df["Compound"] = "MEDIUM"

    lap_df["Compound"] = lap_df["Compound"].fillna("MEDIUM").astype(str).str.upper()
    lap_df.loc[
        ~lap_df["Compound"].isin({"SOFT", "MEDIUM", "HARD", "INTERMEDIATE", "WET"}),
        "Compound",
    ] = "MEDIUM"

    lap_df["Stint"] = pd.to_numeric(lap_df.get("Stint"), errors="coerce").fillna(1).astype(int)

    lap_positions: pd.DataFrame = pd.DataFrame()
    if isinstance(position_df_raw, pd.DataFrame) and not position_df_raw.empty:
        pos_df = position_df_raw.copy()
        pos_df["DriverNumber"] = pos_df["Driver"].astype(str)
        pos_df["Position"] = pd.to_numeric(pos_df.get("Position"), errors="coerce")
        pos_df = pos_df.dropna(subset=["Position"])
        pos_df["Position"] = pos_df["Position"].astype(int)

        lap_token = pos_df.get("GapToLeader", "").astype(str).str.extract(r"LAP\s*(\d+)", expand=False)
        pos_df["LapNumber"] = pd.to_numeric(lap_token, errors="coerce")
        pos_df = pos_df.dropna(subset=["LapNumber"])
        pos_df["LapNumber"] = pos_df["LapNumber"].astype(int)

        if "Time" in pos_df.columns:
            pos_df["Time"] = pd.to_timedelta(pos_df["Time"], errors="coerce")
            pos_df = pos_df.sort_values(by=["DriverNumber", "LapNumber", "Time"])
        else:
            pos_df = pos_df.sort_values(by=["DriverNumber", "LapNumber"])

        lap_positions = pos_df.drop_duplicates(subset=["DriverNumber", "LapNumber"], keep="last")

    if not lap_positions.empty:
        lap_df = lap_df.merge(
            lap_positions[["DriverNumber", "LapNumber", "Position"]],
            on=["DriverNumber", "LapNumber"],
            how="left",
        )
    else:
        lap_df["Position"] = pd.NA

    status_by_lap = _build_track_status_by_lap(session_dir, lap_df)
    lap_df["TrackStatus"] = lap_df["LapNumber"].map(status_by_lap).fillna("1")

    finish_rows = (
        lap_df.sort_values(by=["DriverNumber", "LapNumber", "Time"])
        .groupby("DriverNumber", as_index=False)
        .tail(1)
        .reset_index(drop=True)
    )
    finish_rows = finish_rows.sort_values(by=["LapNumber", "Time"], ascending=[False, True]).reset_index(drop=True)
    finish_rows["Position"] = finish_rows.index + 1

    first_lap = _to_int(lap_df["LapNumber"].min(), 1)
    grid_rows = lap_df[lap_df["LapNumber"] == first_lap].copy()
    grid_rows = grid_rows.dropna(subset=["Position"])
    grid_rows = grid_rows.sort_values(by="Position")

    grid_map: dict[str, int] = {}
    if not grid_rows.empty:
        for _, row in grid_rows.iterrows():
            driver_number = str(row["DriverNumber"])
            grid_map[driver_number] = _to_int(row["Position"], 0)

    result_records: list[dict[str, Any]] = []
    for _, row in finish_rows.iterrows():
        driver_number = str(row["DriverNumber"])
        result_records.append(
            {
                "Abbreviation": number_to_tla.get(driver_number, driver_number),
                "FullName": number_to_name.get(driver_number, driver_number),
                "TeamName": number_to_team.get(driver_number, "Unknown"),
                "DriverNumber": _to_int(driver_number, 0),
                "GridPosition": grid_map.get(driver_number, _to_int(row["Position"], 0)),
                "Position": _to_int(row["Position"], 0),
            }
        )

    results_df = pd.DataFrame(result_records)
    if not results_df.empty:
        results_df = results_df.sort_values(by="Position").reset_index(drop=True)

    weather_df = _build_weather_df(session_dir)

    event = {
        "EventName": _clean_text(cached_race.get("name"), f"{year} Round {round_number}"),
        "Country": cached_race.get("country"),
        "Location": cached_race.get("location"),
        "EventDate": cached_race.get("date"),
    }

    # Keep only the columns used by API analytics, in a stable order.
    columns = [
        "Driver",
        "DriverNumber",
        "LapNumber",
        "LapTime",
        "Time",
        "Compound",
        "Stint",
        "Position",
        "TrackStatus",
    ]
    existing_columns = [column for column in columns if column in lap_df.columns]
    lap_df = lap_df[existing_columns].copy()

    return OfflineSession(event=event, laps=lap_df, results=results_df, weather_data=weather_df)


@lru_cache(maxsize=32)
def get_event_schedule_cached(year: int) -> pd.DataFrame:
    return fastf1.get_event_schedule(year)


def list_supported_years(start_year: int = 2018) -> list[int]:
    now_year = datetime.now(timezone.utc).year
    discovered: set[int] = set()

    for path in CACHE_DIR.iterdir():
        if not path.is_dir():
            continue
        parsed_year = _to_int(path.name, 0)
        if 1950 <= parsed_year <= now_year + 1:
            discovered.add(parsed_year)

    cached_years = [year for year in discovered if year >= start_year]
    cached_years.sort(reverse=True)

    if cached_years:
        return cached_years

    return list(range(now_year, start_year - 1, -1))


def list_races_for_year(year: int) -> list[dict[str, Any]]:
    if year not in _SCHEDULE_UNAVAILABLE_YEARS:
        try:
            schedule = get_event_schedule_cached(year)
            races: list[dict[str, Any]] = []

            for _, row in schedule.iterrows():
                round_number = _to_int(row.get("RoundNumber"), 0)
                if round_number <= 0:
                    continue

                event_date = row.get("EventDate")
                date_iso = None
                if pd.notna(event_date):
                    try:
                        date_iso = pd.to_datetime(event_date).date().isoformat()
                    except Exception:
                        date_iso = None

                races.append(
                    {
                        "round": round_number,
                        "name": str(row.get("EventName", f"Round {round_number}")),
                        "country": str(row.get("Country", "")) or None,
                        "location": str(row.get("Location", "")) or None,
                        "date": date_iso,
                    }
                )

            races.sort(key=lambda race: race["round"])
            if races:
                return races
        except Exception:
            _SCHEDULE_UNAVAILABLE_YEARS.add(year)

    cached = _list_cached_races_with_paths(year)
    return [_public_race_record(race) for race in cached]


@lru_cache(maxsize=24)
def load_race_session(year: int, round_number: int):
    live_exc: Exception | None = None

    if year not in _LIVE_SESSION_UNAVAILABLE_YEARS:
        try:
            session = fastf1.get_session(year, round_number, "R")
            session.load()
            return session
        except Exception as exc:
            _LIVE_SESSION_UNAVAILABLE_YEARS.add(year)
            live_exc = exc

    cached_races = _list_cached_races_with_paths(year)
    race = next((item for item in cached_races if _to_int(item.get("round"), 0) == round_number), None)
    if race is None:
        if live_exc is not None:
            raise live_exc
        raise ValueError(f"No cached race found for year={year}, round={round_number}")
    return _build_offline_session(year, round_number, race)


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

    air_temp = pd.to_numeric(weather_data.get("AirTemp"), errors="coerce").dropna()
    track_temp = pd.to_numeric(weather_data.get("TrackTemp"), errors="coerce").dropna()
    wind_speed = pd.to_numeric(weather_data.get("WindSpeed"), errors="coerce").dropna()
    rainfall = pd.to_numeric(weather_data.get("Rainfall"), errors="coerce").fillna(0)

    rain_probability = float((rainfall > 0).mean()) if len(rainfall) else 0.0

    return {
        "avg_air_temp": round(float(air_temp.mean()) if len(air_temp) else 24.0, 1),
        "avg_track_temp": round(float(track_temp.mean()) if len(track_temp) else 34.0, 1),
        "rain_probability": round(rain_probability, 3),
        "wind_speed_avg": round(float(wind_speed.mean()) if len(wind_speed) else 8.0, 1),
    }
