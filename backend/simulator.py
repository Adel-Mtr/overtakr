import pandas as pd


def simulate_strategy(laps_df, pit_list):
    # Example: fake simulation
    simulated = []
    for i in range(1, len(laps_df) + 1):
        base_time = 90.0 + (i * 0.05)  # fake lap time
        if i in pit_list:
            base_time += 25.0  # pit penalty
        simulated.append(float(base_time))  # ensure Python float
    return simulated
    """
    Very simple mock strategy simulator.
    Assumes each pit adds +20s, and tyres degrade over laps.
    """
    results = []

    for idx, lap in laps_df.iterrows():
        lap_number = int(lap["LapNumber"]) if "LapNumber" in lap else idx + 1
        base_time = float(lap["LapTime"].total_seconds(
        )) if "LapTime" in lap and pd.notna(lap["LapTime"]) else 90.0

        # Check tyre info
        compound = lap["Compound"] if "Compound" in lap and pd.notna(
            lap["Compound"]) else "SOFT"
        stint_age = int(lap["Stint"]) if "Stint" in lap and pd.notna(
            lap["Stint"]) else 1

        # Add tyre degradation (slower over time)
        degraded_time = base_time + (stint_age * 0.05)

        # Add pit stop penalty
        if lap_number in pit_laps:
            degraded_time += 20.0

        results.append({
            "lap": lap_number,
            "time": round(degraded_time, 3),
            "tyre": compound,
            "pit": lap_number in pit_laps
        })

    return results
