"""
Pydantic Models for Smart Charging Optimization.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class VehicleOptimizationInput(BaseModel):
    session_id: str = Field(..., description="Unique vehicle session identifier")
    charger_id: Optional[str] = "EVSE-01"
    arrival_time: str = Field(..., description="ISO arrival timestamp")
    departure_time: str = Field(..., description="ISO departure deadline")
    max_power_kw: float = Field(22.0, gt=0, le=350.0, description="Max power EVSE/vehicle accepts")
    requested_energy_kwh: float = Field(..., ge=0, le=200.0, description="Total energy needed")
    already_delivered_kwh: float = Field(0.0, ge=0.0, description="Energy delivered so far")
    initial_soc_pct: Optional[float] = Field(None, ge=0.0, le=100.0)
    battery_capacity_kwh: Optional[float] = Field(None, gt=0.0)
    priority: int = Field(3, ge=1, le=5, description="Priority weight (1-5)")


class OptimizationRequest(BaseModel):
    station_power_limit_kw: float = Field(150.0, gt=0.0, description="Station transformer capacity limit")
    mode: str = Field("water_filling", description="'water_filling' (instantaneous) or 'advanced_scheduler' (15-min slots)")
    sessions: List[VehicleOptimizationInput] = Field(..., min_length=1, description="List of concurrent EV sessions")
    current_time: Optional[str] = Field(None, description="Current simulation time ISO string")
    tariff_off_peak: Optional[float] = Field(0.12, description="$/kWh off-peak")
    tariff_mid_peak: Optional[float] = Field(0.20, description="$/kWh mid-peak")
    tariff_on_peak: Optional[float] = Field(0.35, description="$/kWh on-peak")


class VehicleAllocationResult(BaseModel):
    session_id: str
    charger_id: str
    allocated_power_kw: float
    max_power_kw: float
    remaining_energy_kwh: float
    estimated_hours_to_complete: float
    estimated_completion_time: str
    departure_deadline: str
    can_complete_before_departure: bool
    unmet_energy_kwh: float
    infeasibility_reason: Optional[str] = None
    priority: int


class TimeSlotScheduleItem(BaseModel):
    slot_index: int
    slot_time: str
    tariff_rate: float
    total_allocated_kw: float
    vehicle_allocations: Dict[str, float]  # session_id -> kw


class OptimizationResponse(BaseModel):
    id: str
    timestamp: str
    mode: str
    station_power_limit_kw: float
    total_requested_energy_kwh: float
    total_allocated_power_kw: float
    unused_capacity_kw: float
    active_vehicles_count: int
    allocations: List[VehicleAllocationResult]
    infeasible_sessions_count: int
    all_demands_feasible: bool
    time_slot_schedule: Optional[List[TimeSlotScheduleItem]] = None
    cost_summary: Dict[str, Any]
