from __future__ import annotations

from dataclasses import dataclass
from math import sin
from typing import Any, Iterable, Sequence

import pandas as pd

COMPOUND_BASE_DELTA = {
    "SOFT": -0.45,
    "MEDIUM": 0.0,
    "HARD": 0.38,
}

COMPOUND_DEGRADATION = {
    "SOFT": 0.062,
    "MEDIUM": 0.046,
    "HARD": 0.031,
}

PROFILE_MULTIPLIER = {
    "aggressive": 1.18,
    "balanced": 1.0,
    "conservative": 0.84,
}

COMPOUND_CYCLE = {
    "SOFT": "MEDIUM",
    "MEDIUM": "HARD",
    "HARD": "SOFT",
}


@dataclass
class StrategySpec:
    name: str
    pit_laps: list[int]
    start_compound: str = "MEDIUM"
    tyre_profile: str = "balanced"
    fuel_save: float = 0.0


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def parse_pit_laps(value: Any) -> list[int]:
    if value is None:
        return []

    if isinstance(value, str):
        parsed = [_safe_int(part.strip(), -1) for part in value.split(",")]
    elif isinstance(value, Iterable):
        parsed = [_safe_int(item, -1) for item in value]
    else:
        parsed = []

    unique = sorted({lap for lap in parsed if lap > 0})
    return unique


def _seconds_from_laptime(value: Any) -> float | None:
    if value is None or pd.isna(value):
        return None

    if hasattr(value, "total_seconds"):
        seconds = _safe_float(value.total_seconds(), -1.0)
    else:
        seconds = _safe_float(value, -1.0)

    if seconds <= 0:
        return None
    return seconds


def _median_lap_times(laps_df: pd.DataFrame) -> dict[int, float]:
    lap_medians: dict[int, float] = {}
    if "LapNumber" not in laps_df.columns or "LapTime" not in laps_df.columns:
        return lap_medians

    grouped = laps_df.groupby("LapNumber")

    for lap_number, group in grouped:
        lap = _safe_int(lap_number, 0)
        if lap <= 0:
            continue

        seconds = [
            sec
            for sec in (_seconds_from_laptime(v) for v in group["LapTime"])
            if sec is not None
        ]

        if not seconds:
            continue

        series = pd.Series(seconds, dtype="float64")
        if len(series) > 5:
            low = float(series.quantile(0.1))
            high = float(series.quantile(0.9))
            series = series[(series >= low) & (series <= high)]

        lap_medians[lap] = round(float(series.median()), 3)

    return lap_medians


def build_baseline_laps(laps_df: pd.DataFrame, driver: str | None = None) -> tuple[list[float], str]:
    if laps_df.empty or "LapNumber" not in laps_df.columns:
        return [], "none"

    total_laps = _safe_int(laps_df["LapNumber"].max(), 0)
    if total_laps <= 0:
        return [], "none"

    full_medians = _median_lap_times(laps_df)
    source_df = laps_df
    source_label = "field-median"

    if driver and "Driver" in laps_df.columns:
        driver_df = laps_df[laps_df["Driver"] == driver]
        if not driver_df.empty:
            source_df = driver_df
            source_label = f"driver:{driver}"

    source_medians = _median_lap_times(source_df)

    baseline: list[float] = []
    fallback_time = 91.0

    for lap in range(1, total_laps + 1):
        lap_time = source_medians.get(lap)
        if lap_time is None:
            lap_time = full_medians.get(lap)

        if lap_time is None:
            lap_time = baseline[-1] + 0.12 if baseline else fallback_time

        if baseline:
            lap_time = min(lap_time, baseline[-1] + 2.5)

        baseline.append(round(max(65.0, lap_time), 3))

    return baseline, source_label


def normalize_strategy(raw: dict[str, Any]) -> StrategySpec:
    name = str(raw.get("name", "Strategy")).strip() or "Strategy"
    pit_laps = parse_pit_laps(raw.get("pit_laps"))

    start_compound = str(raw.get("start_compound", "MEDIUM")).upper()
    if start_compound not in COMPOUND_BASE_DELTA:
        start_compound = "MEDIUM"

    tyre_profile = str(raw.get("tyre_profile", "balanced")).lower()
    if tyre_profile not in PROFILE_MULTIPLIER:
        tyre_profile = "balanced"

    fuel_save = _safe_float(raw.get("fuel_save"), 0.0)
    fuel_save = max(-0.8, min(1.5, fuel_save))

    return StrategySpec(
        name=name,
        pit_laps=pit_laps,
        start_compound=start_compound,
        tyre_profile=tyre_profile,
        fuel_save=fuel_save,
    )


def simulate_single_strategy(
    base_laps: Sequence[float],
    strategy: StrategySpec,
    pit_penalty: float,
    safety_car_laps: set[int],
    weather_risk: float,
) -> dict[str, Any]:
    pit_penalty = max(14.0, min(32.0, _safe_float(pit_penalty, 21.5)))
    weather_risk = max(0.0, min(1.0, _safe_float(weather_risk, 0.0)))

    current_compound = strategy.start_compound
    stint_age = 0
    stint_start = 1
    pits = set(strategy.pit_laps)
    cumulative = 0.0

    laps: list[dict[str, Any]] = []
    stints: list[dict[str, Any]] = []

    for lap_index, base_lap_time in enumerate(base_laps, start=1):
        profile_mult = PROFILE_MULTIPLIER[strategy.tyre_profile]
        degradation = COMPOUND_DEGRADATION[current_compound] * profile_mult * stint_age
        compound_delta = COMPOUND_BASE_DELTA[current_compound]

        traffic_wave = sin((lap_index + len(strategy.name)) * 0.34) * 0.11
        weather_penalty = weather_risk * (0.10 + 0.015 * lap_index)

        lap_time = (
            base_lap_time
            + compound_delta
            + degradation
            + strategy.fuel_save
            + traffic_wave
            + weather_penalty
        )

        pit_stop = lap_index in pits
        safety_car = lap_index in safety_car_laps

        if pit_stop:
            pit_discount = 0.62 if safety_car else 1.0
            lap_time += pit_penalty * pit_discount

        lap_time = round(max(65.0, float(lap_time)), 3)
        cumulative = round(cumulative + lap_time, 3)

        laps.append(
            {
                "lap": lap_index,
                "lap_time": lap_time,
                "cumulative": cumulative,
                "compound": current_compound,
                "pit": pit_stop,
                "safety_car": safety_car,
                "degradation": round(float(degradation), 3),
            }
        )

        if pit_stop:
            stints.append(
                {
                    "compound": current_compound,
                    "start_lap": stint_start,
                    "end_lap": lap_index,
                    "laps": lap_index - stint_start + 1,
                }
            )
            current_compound = COMPOUND_CYCLE[current_compound]
            stint_start = lap_index + 1
            stint_age = 0
        else:
            stint_age += 1

    total_laps = len(base_laps)
    if total_laps > 0 and stint_start <= total_laps:
        stints.append(
            {
                "compound": current_compound,
                "start_lap": stint_start,
                "end_lap": total_laps,
                "laps": total_laps - stint_start + 1,
            }
        )

    total_time = round(float(cumulative), 3)
    avg_lap = round(total_time / total_laps, 3) if total_laps else 0.0

    return {
        "total_time": total_time,
        "average_lap": avg_lap,
        "pits": len(pits),
        "stints": stints,
        "laps": laps,
    }


def build_leaderboard(strategies: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    if not strategies:
        return []

    best_time = min(float(item["total_time"]) for item in strategies.values())
    rows: list[dict[str, Any]] = []

    for name, data in strategies.items():
        total_time = float(data["total_time"])
        rows.append(
            {
                "name": name,
                "total_time": round(total_time, 3),
                "gap_to_best": round(total_time - best_time, 3),
                "pits": int(data.get("pits", 0)),
                "avg_lap": round(float(data.get("average_lap", 0.0)), 3),
            }
        )

    rows.sort(key=lambda row: row["total_time"])
    return rows


def recommend_pit_windows(
    base_laps: Sequence[float],
    pit_penalty: float,
    safety_car_laps: set[int],
) -> list[dict[str, Any]]:
    if len(base_laps) < 15:
        return []

    windows: list[dict[str, Any]] = []
    last_lap = len(base_laps)

    for lap in range(8, last_lap - 5):
        tyre_saving_projection = (last_lap - lap) * (0.028 + (lap / last_lap) * 0.02)
        pit_discount = 0.62 if lap in safety_car_laps else 1.0
        penalty_projection = pit_penalty * pit_discount * 0.11
        sc_bonus = 1.9 if lap in safety_car_laps else 0.0

        score = round(tyre_saving_projection - penalty_projection + sc_bonus, 3)
        windows.append(
            {
                "lap": lap,
                "score": score,
                "label": "Safety car window" if lap in safety_car_laps else "Green flag window",
            }
        )

    windows.sort(key=lambda item: item["score"], reverse=True)
    return windows[:5]


def simulate_strategy(laps_df: pd.DataFrame, pit_list: list[int]) -> list[float]:
    """Backward-compatible helper used by older code paths."""
    baseline, _ = build_baseline_laps(laps_df)
    strategy = StrategySpec(name="Strategy", pit_laps=parse_pit_laps(pit_list))
    simulated = simulate_single_strategy(
        base_laps=baseline,
        strategy=strategy,
        pit_penalty=21.5,
        safety_car_laps=set(),
        weather_risk=0.0,
    )
    return [float(lap["lap_time"]) for lap in simulated["laps"]]
