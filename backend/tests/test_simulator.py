import pandas as pd

from simulator import (
    StrategySpec,
    build_baseline_laps,
    build_leaderboard,
    parse_pit_laps,
    simulate_single_strategy,
)


def test_parse_pit_laps_deduplicates_and_sorts():
    assert parse_pit_laps("39, 18, 18") == [18, 39]


def test_build_baseline_laps_prefers_selected_driver():
    laps = pd.DataFrame(
        {
            "Driver": ["AAA", "BBB", "AAA", "BBB"],
            "LapNumber": [1, 1, 2, 2],
            "LapTime": [pd.Timedelta(seconds=90), pd.Timedelta(seconds=92), pd.Timedelta(seconds=89), pd.Timedelta(seconds=91)],
        }
    )

    baseline, source = build_baseline_laps(laps, driver="AAA")

    assert source == "driver:AAA"
    assert baseline == [90.0, 89.0]


def test_simulation_applies_pit_penalty_and_builds_stints():
    strategy = StrategySpec(name="One stop", pit_laps=[2], start_compound="MEDIUM")
    result = simulate_single_strategy(
        base_laps=[90.0, 90.0, 90.0, 90.0],
        strategy=strategy,
        pit_penalty=20.0,
        safety_car_laps=set(),
        weather_risk=0.0,
    )

    assert result["pits"] == 1
    assert result["laps"][1]["pit"] is True
    assert len(result["stints"]) == 2
    assert result["laps"][1]["lap_time"] > result["laps"][0]["lap_time"] + 15


def test_leaderboard_orders_fastest_first():
    leaderboard = build_leaderboard(
        {
            "Slow": {"total_time": 101.0, "pits": 1, "average_lap": 50.5},
            "Fast": {"total_time": 99.0, "pits": 1, "average_lap": 49.5},
        }
    )

    assert [row["name"] for row in leaderboard] == ["Fast", "Slow"]
    assert leaderboard[1]["gap_to_best"] == 2.0
