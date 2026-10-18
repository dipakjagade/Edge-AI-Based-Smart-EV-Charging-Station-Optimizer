"""
Pydantic Models for Demand Prediction.
"""

from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field


class PredictionRequest(BaseModel):
    hour: int = Field(..., ge=0, le=23, description="Hour of day (0-23)")
    day_of_week: int = Field(..., ge=0, le=6, description="Day of week (0=Mon, 6=Sun)")
    is_weekend: Optional[int] = Field(None, ge=0, le=1)
    active_sessions: int = Field(..., ge=0, le=50, description="Concurrent EV sessions")
    total_requested_energy_kwh: float = Field(..., ge=0.0, description="Sum of requested energy (kWh)")
    avg_battery_soc: float = Field(..., ge=0.0, le=100.0, description="Average incoming battery SOC (%)")
    tariff_rate: float = Field(0.20, gt=0.0, description="Current electricity tariff ($/kWh)")
    lagged_demand_1h_kw: Optional[float] = Field(None, ge=0.0, description="Actual demand 1 hour ago (kW)")
    lagged_demand_24h_kw: Optional[float] = Field(None, ge=0.0, description="Actual demand 24 hours ago (kW)")
    rolling_mean_3h_kw: Optional[float] = Field(None, ge=0.0, description="Rolling 3-hour mean demand (kW)")
    station_capacity_kw: Optional[float] = Field(150.0, gt=0.0, description="Station transformer rating")


class PredictionResponse(BaseModel):
    id: str
    predicted_demand_kw: float
    confidence_interval: Dict[str, float]  # e.g. {"lower_kw": 45.2, "upper_kw": 58.6}
    baseline_prediction_kw: float
    model_version: str
    model_type: str
    fallback_used: bool
    warning: Optional[str] = None
    input_features: Dict[str, Any]
    capacity_exceeded: bool
    capacity_headroom_kw: float
    timestamp: str
