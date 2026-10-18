"""
Automated Tests for Edge AI Model Training, Inference, and Fallbacks.
"""

import os
import pytest
from app.services.ml_service import ml_service, MLService
from app.models.prediction import PredictionRequest


def test_model_loaded_and_predicts():
    """Verify saved Random Forest model performs inference."""
    assert ml_service.is_loaded is True
    assert ml_service.model is not None

    req = PredictionRequest(
        hour=14,
        day_of_week=2,
        active_sessions=6,
        total_requested_energy_kwh=180.0,
        avg_battery_soc=35.0,
        tariff_rate=0.35,
        station_capacity_kw=150.0
    )
    res = ml_service.predict_demand(req)
    assert res.predicted_demand_kw > 0.0
    assert res.predicted_demand_kw <= 150.0
    assert res.confidence_interval["lower_kw"] <= res.predicted_demand_kw
    assert res.confidence_interval["upper_kw"] >= res.predicted_demand_kw
    assert res.model_type == "RandomForestRegressor"
    assert res.fallback_used is False


def test_zero_sessions_zero_demand():
    """When active sessions are 0, predicted demand must be exactly 0 kW."""
    req = PredictionRequest(
        hour=2,
        day_of_week=0,
        active_sessions=0,
        total_requested_energy_kwh=0.0,
        avg_battery_soc=50.0,
        tariff_rate=0.12,
        station_capacity_kw=150.0
    )
    res = ml_service.predict_demand(req)
    assert res.predicted_demand_kw == 0.0
    assert res.confidence_interval["lower_kw"] == 0.0


def test_safe_conservative_fallback_mode(monkeypatch):
    """When model file is missing, the service must safely fall back to conservative heuristics."""
    fallback_svc = MLService()
    fallback_svc.model = None
    fallback_svc.is_loaded = False

    req = PredictionRequest(
        hour=18,
        day_of_week=4,
        active_sessions=5,
        total_requested_energy_kwh=150.0,
        avg_battery_soc=30.0,
        tariff_rate=0.35,
        station_capacity_kw=150.0
    )
    res = fallback_svc.predict_demand(req)
    assert res.fallback_used is True
    assert "fallback" in res.warning.lower()
    assert res.predicted_demand_kw > 0.0
    assert res.predicted_demand_kw <= 150.0
