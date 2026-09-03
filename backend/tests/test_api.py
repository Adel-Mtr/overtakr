from datetime import datetime, timezone

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_root_exposes_service_links():
    response = client.get("/")

    assert response.status_code == 200
    payload = response.json()
    assert payload["service"] == "overtakr-api"
    assert payload["docs"] == "/docs"
    assert payload["health"] == "/api/health"


def test_health_is_available_without_loading_race_data():
    response = client.get("/api/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["service"] == "overtakr-api"
    assert payload["version"]


def test_supported_years_include_current_season():
    response = client.get("/api/years")

    assert response.status_code == 200
    years = response.json()["years"]
    assert years[0] == datetime.now(timezone.utc).year
    assert 2018 in years


def test_duplicate_strategy_names_are_rejected_before_data_load():
    response = client.post(
        "/api/simulate",
        json={
            "year": 2024,
            "round": 1,
            "strategies": [
                {"name": "Plan A", "pit_laps": "18"},
                {"name": "plan a", "pit_laps": "22"},
            ],
        },
    )

    assert response.status_code == 422
    assert "strategy names must be unique" in response.text


def test_invalid_pit_lap_syntax_is_rejected_before_data_load():
    response = client.post(
        "/api/simulate",
        json={
            "year": 2024,
            "round": 1,
            "strategies": [{"name": "Plan A", "pit_laps": "18,abc"}],
        },
    )

    assert response.status_code == 422
    assert "pit_laps" in response.text
