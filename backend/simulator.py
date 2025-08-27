# backend/simulator.py
def simulate_strategy(laps_df, pit_laps=None):
    """
    Simple simulation: adjust lap times for pit stops and tyre degradation.
    pit_laps: list of lap numbers where pit stops happen
    """
    if pit_laps is None:
        pit_laps = []

    deg_rate = {'SOFT': 0.12, 'MEDIUM': 0.08, 'HARD': 0.05}  # sec per lap
    results = []

    for _, lap in laps_df.iterrows():
        lap_time = lap['LapTime'].total_seconds()
        compound = lap['Compound'] if 'Compound' in lap else 'SOFT'
        tyre_age = lap['Stint'] if 'Stint' in lap else 1  # simple example
        lap_time += deg_rate.get(compound.upper(), 0) * tyre_age

        if lap['LapNumber'] in pit_laps:
            lap_time += 22.5  # pit stop time loss in seconds

        results.append({
            "lap": lap['LapNumber'],
            "driver_code": lap['Driver'],
            "simulated_time": round(lap_time, 3)
        })
    return results
