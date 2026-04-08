"""
Test suite for UAV Fleet Monitoring API routes.
"""

import pytest
from app.routes import app as flask_app


@pytest.fixture
def app():
    flask_app.config["TESTING"] = True
    flask_app.config["DEBUG"] = False
    yield flask_app


@pytest.fixture
def client(app):
    yield app.test_client()


# ─── /health ──────────────────────────────────────────────────────────────────

def test_health_returns_200(client):
    response = client.get("/health")
    assert response.status_code == 200


def test_health_has_required_fields(client):
    response = client.get("/health")
    data = response.get_json()
    assert "status" in data
    assert "drone_count" in data
    assert "timestamp" in data
    assert "uptime_seconds" in data
    assert data["status"] == "ok"
    assert data["drone_count"] == 5


# ─── /drones ──────────────────────────────────────────────────────────────────

def test_drones_returns_200(client):
    response = client.get("/drones")
    assert response.status_code == 200


def test_drones_returns_exactly_five(client):
    response = client.get("/drones")
    data = response.get_json()
    assert isinstance(data, list)
    assert len(data) == 5


def test_all_drones_have_required_fields(client):
    response = client.get("/drones")
    drones = response.get_json()
    required = [
        "id", "lat", "lon", "battery", "altitude", "speed",
        "heading", "status", "mission", "signal_strength",
        "threat_level", "flight_time_seconds",
    ]
    for drone in drones:
        for field in required:
            assert field in drone, f"Field '{field}' missing from drone {drone.get('id')}"


def test_drone_status_is_valid_enum(client):
    response = client.get("/drones")
    drones = response.get_json()
    valid_statuses = {"ACTIVE", "RETURNING", "LOW_BATTERY", "OFFLINE"}
    for drone in drones:
        assert drone["status"] in valid_statuses, (
            f"Drone {drone['id']} has invalid status: {drone['status']}"
        )


def test_drone_battery_in_range(client):
    response = client.get("/drones")
    drones = response.get_json()
    for drone in drones:
        assert 0.0 <= drone["battery"] <= 100.0, (
            f"Drone {drone['id']} battery out of range: {drone['battery']}"
        )


def test_drone_signal_in_range(client):
    response = client.get("/drones")
    drones = response.get_json()
    for drone in drones:
        assert 0 <= drone["signal_strength"] <= 100, (
            f"Drone {drone['id']} signal out of range: {drone['signal_strength']}"
        )


def test_lat_lon_are_floats(client):
    response = client.get("/drones")
    drones = response.get_json()
    for drone in drones:
        assert isinstance(drone["lat"], float), (
            f"Drone {drone['id']} lat is not float: {type(drone['lat'])}"
        )
        assert isinstance(drone["lon"], float), (
            f"Drone {drone['id']} lon is not float: {type(drone['lon'])}"
        )


# ─── /drones/<id>/telemetry ───────────────────────────────────────────────────

def test_telemetry_valid_id(client):
    response = client.get("/drones/UAV-001/telemetry")
    assert response.status_code == 200
    data = response.get_json()
    assert "battery" in data


def test_telemetry_invalid_id(client):
    response = client.get("/drones/FAKE-999/telemetry")
    assert response.status_code == 404


def test_telemetry_404_has_error_field(client):
    response = client.get("/drones/FAKE-999/telemetry")
    data = response.get_json()
    assert "error" in data


# ─── /drones/<id>/history ─────────────────────────────────────────────────────

def test_drone_history_valid_id(client):
    response = client.get("/drones/UAV-001/history")
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)


def test_drone_history_invalid_id(client):
    response = client.get("/drones/FAKE-999/history")
    assert response.status_code == 404


# ─── /fleet/summary ───────────────────────────────────────────────────────────

def test_fleet_summary_returns_200(client):
    response = client.get("/fleet/summary")
    assert response.status_code == 200


def test_fleet_summary_has_all_fields(client):
    response = client.get("/fleet/summary")
    data = response.get_json()
    required = [
        "total", "active", "returning", "low_battery", "offline",
        "avg_battery", "avg_altitude", "avg_speed", "fleet_threat_level",
    ]
    for field in required:
        assert field in data, f"Summary missing field: '{field}'"


def test_fleet_total_equals_five(client):
    response = client.get("/fleet/summary")
    data = response.get_json()
    assert data["total"] == 5


# ─── Error handlers ───────────────────────────────────────────────────────────

def test_404_returns_json(client):
    response = client.get("/nonexistent")
    assert response.status_code == 404
    assert "application/json" in response.content_type
    data = response.get_json()
    assert "error" in data
