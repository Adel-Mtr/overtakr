import fastf1
import os

# Ensure cache folder exists
CACHE_DIR = os.path.join(os.getcwd(), "ff1cache")
os.makedirs(CACHE_DIR, exist_ok=True)
fastf1.Cache.enable_cache(CACHE_DIR)


def get_race_laps(year: int, round: int):
    """
    Fetch race laps from FastF1 for given year and round.
    Returns pandas DataFrame with laps.
    Raises ValueError with explanation if something goes wrong.
    """
    try:
        session = fastf1.get_session(year, round, 'R')
        session.load()  # May take time (downloads data into cache)
        laps_df = session.laps

        if laps_df.empty:
            raise ValueError(f"No laps found for {year} Round {round}")

        return laps_df

    except Exception as e:
        raise ValueError(f"Failed to load race session: {e}")
