import pandas as pd
import pytest

import fastf1_utils


class LoadedSession:
    def __init__(self):
        self.loaded_with = None
        self.laps = pd.DataFrame({"LapNumber": [1]})
        self.results = pd.DataFrame({"Position": [1]})

    def load(self, **kwargs):
        self.loaded_with = kwargs


class IncompleteSession:
    def load(self, **kwargs):
        self.loaded_with = kwargs

    @property
    def laps(self):
        raise RuntimeError("laps unavailable")

    @property
    def results(self):
        return pd.DataFrame()


def test_load_race_session_disables_telemetry(monkeypatch):
    session = LoadedSession()
    monkeypatch.setattr(fastf1_utils.fastf1, "get_session", lambda *_args: session)
    fastf1_utils.load_race_session.cache_clear()

    loaded = fastf1_utils.load_race_session(2024, 1)

    assert loaded is session
    assert session.loaded_with == {"telemetry": False, "weather": True, "messages": True}


def test_load_race_session_surfaces_missing_required_data(monkeypatch):
    session = IncompleteSession()
    monkeypatch.setattr(fastf1_utils.fastf1, "get_session", lambda *_args: session)
    fastf1_utils.load_race_session.cache_clear()

    with pytest.raises(RuntimeError, match="laps unavailable"):
        fastf1_utils.load_race_session(2024, 1)
