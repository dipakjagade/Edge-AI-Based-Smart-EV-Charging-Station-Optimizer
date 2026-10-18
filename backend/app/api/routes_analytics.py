"""
Demand and Cost Analytics API Routes.
"""

from typing import Dict, Any
from fastapi import APIRouter, Query
from app.config import settings
from app.services.tariff_service import tariff_service
import pandas as pd
import numpy as np

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])


@router.get("/demand")
def get_demand_analytics(days: int = Query(7, ge=1, le=30)) -> Dict[str, Any]:
    """Provides demand time series trends, peak hours, and diurnal profile for charts."""
    # 24-hour diurnal profile
    hours = list(range(24))
    hourly_trends = []
    
    for h in hours:
        # Realistic diurnal pattern: morning peak at 8am, evening commute peak at 6pm
        m_peak = np.exp(-0.5 * ((h - 8.5) / 1.5) ** 2)
        e_peak = np.exp(-0.5 * ((h - 18.0) / 2.0) ** 2)
        midday = 0.4 * np.exp(-0.5 * ((h - 13.0) / 3.0) ** 2)
        expected_demand = float(round(12.0 + 115.0 * (m_peak * 0.85 + e_peak * 0.95 + midday), 1))
        station_limit = settings.DEFAULT_STATION_CAPACITY_KW
        
        hourly_trends.append({
            "hour": f"{h:02d}:00",
            "hour_num": h,
            "average_demand_kw": expected_demand,
            "peak_demand_kw": min(station_limit * 1.1, round(expected_demand * 1.25, 1)),
            "min_demand_kw": round(expected_demand * 0.75, 1),
            "station_capacity_kw": station_limit,
            "overload_risk": expected_demand > station_limit
        })

    return {
        "timeframe_days": days,
        "station_capacity_kw": settings.DEFAULT_STATION_CAPACITY_KW,
        "peak_hour": "18:00 (Evening Commute Peak)",
        "trough_hour": "03:00 (Night Valley)",
        "average_daily_energy_kwh": 1420.0,
        "load_factor": 0.58,
        "hourly_diurnal_curve": hourly_trends
    }


@router.get("/cost")
def get_cost_analytics(
    energy_kwh: float = Query(350.0, gt=0, le=5000.0, description="Daily charging energy delivered"),
    station_limit_kw: float = Query(150.0, gt=0, description="Station power rating")
) -> Dict[str, Any]:
    """Compares uncontrolled charging, basic power allocation, and advanced time-of-use scheduling."""
    comparison = tariff_service.calculate_cost_comparison(
        energy_kwh=energy_kwh,
        uncontrolled_peak_kw=station_limit_kw * 1.25,
        optimized_peak_kw=station_limit_kw * 0.85,
        station_limit_kw=station_limit_kw
    )
    return comparison
