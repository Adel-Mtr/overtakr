# backend/fastf1_utils.py
import fastf1
import os

# Ensure cache folder exists
CACHE_DIR = os.path.join(os.getcwd(), "ff1cache")
os.makedirs(CACHE_DIR, exist_ok=True)
fastf1.Cache.enable_cache(CACHE_DIR)

def get_race_laps(year: int, round: int):
    """
    Fetch race laps from FastF1 for given year and round.
    Returns a pandas DataFrame with laps.
    """
    session = fastf1.get_session(year, round, 'R')
    session.load()
    laps_df = session.laps
    return laps_df
