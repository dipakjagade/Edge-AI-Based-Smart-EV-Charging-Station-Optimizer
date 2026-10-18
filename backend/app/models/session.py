"""
Pydantic Models for EV Charging Sessions.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator


class SessionCreate(BaseModel):
    session_id: str = Field(..., description="Unique vehicle/session identifier", min_length=2, max_length=50)
    charger_id: Optional[str] = Field("EVSE-01", description="Charger stall ID")
    arrival_time: str = Field(..., description="Arrival ISO timestamp (e.g. 2026-10-18T08:00:00)")
    departure_time: str = Field(..., description="Departure deadline ISO timestamp (e.g. 2026-10-18T12:00:00)")
    max_power_kw: float = Field(22.0, gt=0, le=350.0, description="Max charging rate accepted by EV (kW)")
    requested_energy_kwh: float = Field(..., ge=0, le=200.0, description="Energy target in kWh")
    initial_soc_pct: Optional[float] = Field(None, ge=0.0, le=100.0, description="Initial State of Charge (%)")
    battery_capacity_kwh: Optional[float] = Field(None, gt=0, le=250.0, description="EV battery pack size (kWh)")
    priority: int = Field(3, ge=1, le=5, description="Scheduling priority (1=Lowest, 5=Emergency/VIP)")
    status: str = Field("active", description="Status: pending, active, completed, cancelled")

    @field_validator("departure_time")
    @classmethod
    def validate_departure_after_arrival(cls, v, info):
        arrival_str = info.data.get("arrival_time")
        if arrival_str and v:
            try:
                arr = datetime.fromisoformat(arrival_str)
                dep = datetime.fromisoformat(v)
                if dep <= arr:
                    raise ValueError("Departure deadline must be chronologically after arrival time.")
            except ValueError as e:
                if "Departure deadline must be" in str(e):
                    raise e
        return v


class SessionUpdate(BaseModel):
    charger_id: Optional[str] = None
    departure_time: Optional[str] = None
    max_power_kw: Optional[float] = None
    requested_energy_kwh: Optional[float] = None
    priority: Optional[int] = None
    status: Optional[str] = None


class SessionResponse(BaseModel):
    id: str
    session_id: str
    charger_id: str
    arrival_time: str
    departure_time: str
    max_power_kw: float
    requested_energy_kwh: float
    delivered_energy_kwh: float = 0.0
    initial_soc_pct: Optional[float] = None
    current_soc_pct: Optional[float] = None
    battery_capacity_kwh: Optional[float] = None
    priority: int
    status: str
    allocated_power_kw: float = 0.0
    remaining_hours: float = 0.0
    minimum_required_power_kw: float = 0.0
    is_achievable: bool = True
    created_at: str
