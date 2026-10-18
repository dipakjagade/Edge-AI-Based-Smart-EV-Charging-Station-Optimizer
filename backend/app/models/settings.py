"""
Pydantic Models for Application Settings and Alerts.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class TariffTier(BaseModel):
    name: str = "Mid-Peak"
    start_hour: int = Field(6, ge=0, le=23)
    end_hour: int = Field(14, ge=0, le=24)
    rate_usd_per_kwh: float = Field(0.20, gt=0.0)


class StationSettings(BaseModel):
    station_name: str = "Antigravity Edge EV Hub #1"
    station_power_limit_kw: float = Field(150.0, gt=0.0, le=2000.0)
    total_chargers: int = Field(10, ge=1, le=100)
    default_charger_limit_kw: float = Field(22.0, gt=0.0, le=350.0)
    currency: str = "USD"
    tariffs: List[TariffTier] = [
        TariffTier(name="Off-Peak", start_hour=22, end_hour=6, rate_usd_per_kwh=0.12),
        TariffTier(name="Mid-Peak", start_hour=6, end_hour=14, rate_usd_per_kwh=0.20),
        TariffTier(name="On-Peak", start_hour=14, end_hour=20, rate_usd_per_kwh=0.35),
        TariffTier(name="Mid-Peak Evening", start_hour=20, end_hour=22, rate_usd_per_kwh=0.20),
    ]
    demo_mode: bool = True
    edge_mode: bool = True
    coincident_peak_penalty_usd_per_kw: float = 12.50


class AlertItem(BaseModel):
    id: str
    severity: str  # "info", "warning", "critical"
    title: str
    message: str
    source: str    # "prediction", "optimizer", "edge_health", "database"
    timestamp: str
    resolved: bool = False
