"""
Smart Charging Optimizer API Routes.
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from app.models.optimization import OptimizationRequest, OptimizationResponse, VehicleOptimizationInput
from app.services.optimizer_service import optimizer_service
from app.database import db_manager

router = APIRouter(prefix="/api", tags=["Smart Charging Optimizer"])


@router.post("/optimize", response_model=OptimizationResponse)
def run_optimization(req: OptimizationRequest):
    """
    Allocate charging power across active EV sessions under station capacity constraints.
    Supports 'water_filling' or 'advanced_scheduler'.
    """
    try:
        response = optimizer_service.optimize(req)
        return response
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Optimizer error: {str(e)}")


@router.post("/optimize/active-sessions", response_model=OptimizationResponse)
def optimize_current_active_sessions(
    mode: str = Query("water_filling", description="'water_filling' or 'advanced_scheduler'"),
    station_power_limit_kw: float = Query(150.0, description="Station capacity limit in kW")
):
    """
    Convenience endpoint: pulls all currently active EV sessions from the database
    and optimizes their charging power allocation.
    """
    sessions_col = db_manager.get_collection("sessions")
    active_docs = sessions_col.find({"status": "active"})
    
    if not active_docs:
        raise HTTPException(status_code=400, detail="No active EV sessions found in database to optimize.")
        
    inputs = [
        VehicleOptimizationInput(
            session_id=d["session_id"],
            charger_id=d.get("charger_id", "EVSE-01"),
            arrival_time=d["arrival_time"],
            departure_time=d["departure_time"],
            max_power_kw=float(d.get("max_power_kw", 22.0)),
            requested_energy_kwh=float(d.get("requested_energy_kwh", 30.0)),
            already_delivered_kwh=float(d.get("delivered_energy_kwh", 0.0)),
            initial_soc_pct=d.get("initial_soc_pct"),
            battery_capacity_kwh=d.get("battery_capacity_kwh"),
            priority=int(d.get("priority", 3))
        )
        for d in active_docs
    ]
    
    req = OptimizationRequest(
        station_power_limit_kw=station_power_limit_kw,
        mode=mode,
        sessions=inputs
    )
    
    result = optimizer_service.optimize(req)
    
    # Update active sessions in database with newly allocated power
    for alloc in result.allocations:
        sessions_col.update_one(
            {"session_id": alloc.session_id},
            {"$set": {"allocated_power_kw": alloc.allocated_power_kw}}
        )
        
    return result


@router.get("/optimizations", response_model=List[OptimizationResponse])
def get_optimization_history(limit: int = 50):
    col = db_manager.get_collection("optimizations")
    results = col.find()
    reversed_results = list(reversed(results))[:limit]
    return [OptimizationResponse(**r) for r in reversed_results]


@router.get("/optimizations/{id}", response_model=OptimizationResponse)
def get_single_optimization(id: str):
    col = db_manager.get_collection("optimizations")
    doc = col.find_one({"id": id}) or col.find_one({"_id": id})
    if not doc:
        raise HTTPException(status_code=404, detail=f"Optimization record '{id}' not found.")
    return OptimizationResponse(**doc)
