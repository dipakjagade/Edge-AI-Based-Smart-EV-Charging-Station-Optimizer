"""
Integration Tests for FastAPI Endpoints.
"""

from datetime import datetime, timedelta
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_check_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "service" in data


def test_dashboard_summary_endpoint():
    response = client.get("/api/dashboard/summary")
    assert response.status_code == 200
    data = response.json()
    assert "station_capacity_kw" in data
    assert "allocated_power_kw" in data
    assert "active_sessions_count" in data
    assert data["demo_mode"] is True


def test_sessions_crud_flow():
    now = datetime.now()
    unique_id = f"TEST-EV-{int(now.timestamp())}"
    
    # Create session
    payload = {
        "session_id": unique_id,
        "charger_id": "EVSE-09",
        "arrival_time": now.isoformat(),
        "departure_time": (now + timedelta(hours=3)).isoformat(),
        "max_power_kw": 22.0,
        "requested_energy_kwh": 36.0,
        "initial_soc_pct": 20.0,
        "battery_capacity_kwh": 75.0,
        "priority": 4,
        "status": "active"
    }
    create_res = client.post("/api/sessions", json=payload)
    assert create_res.status_code == 201
    created_data = create_res.json()
    assert created_data["session_id"] == unique_id
    
    # Duplicate session creation must fail
    dup_res = client.post("/api/sessions", json=payload)
    assert dup_res.status_code == 400

    # Get single session
    get_res = client.get(f"/api/sessions/{unique_id}")
    assert get_res.status_code == 200
    assert get_res.json()["session_id"] == unique_id

    # Update session
    update_res = client.put(f"/api/sessions/{unique_id}", json={"priority": 5})
    assert update_res.status_code == 200
    assert update_res.json()["priority"] == 5

    # Delete session
    del_res = client.delete(f"/api/sessions/{unique_id}")
    assert del_res.status_code == 200


def test_prediction_endpoint():
    payload = {
        "hour": 15,
        "day_of_week": 3,
        "active_sessions": 7,
        "total_requested_energy_kwh": 210.0,
        "avg_battery_soc": 32.0,
        "tariff_rate": 0.35,
        "station_capacity_kw": 150.0
    }
    res = client.post("/api/predict", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "predicted_demand_kw" in data
    assert data["predicted_demand_kw"] > 0.0


def test_optimization_endpoint():
    now = datetime.now()
    payload = {
        "station_power_limit_kw": 120.0,
        "mode": "water_filling",
        "sessions": [
            {
                "session_id": "TEST-OPT-1",
                "arrival_time": now.isoformat(),
                "departure_time": (now + timedelta(hours=2)).isoformat(),
                "max_power_kw": 22.0,
                "requested_energy_kwh": 30.0,
                "priority": 3
            },
            {
                "session_id": "TEST-OPT-2",
                "arrival_time": now.isoformat(),
                "departure_time": (now + timedelta(hours=1, minutes=30)).isoformat(),
                "max_power_kw": 50.0,
                "requested_energy_kwh": 40.0,
                "priority": 5
            }
        ]
    }
    res = client.post("/api/optimize", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["total_allocated_power_kw"] <= 120.0
    assert len(data["allocations"]) == 2


def test_analytics_endpoints():
    demand_res = client.get("/api/analytics/demand")
    assert demand_res.status_code == 200
    assert len(demand_res.json()["hourly_diurnal_curve"]) == 24

    cost_res = client.get("/api/analytics/cost?energy_kwh=300")
    assert cost_res.status_code == 200
    assert "comparison_summary" in cost_res.json()
