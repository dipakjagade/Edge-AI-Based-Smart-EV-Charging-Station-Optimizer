"""
EV Charging Session Management API Routes.
"""

import uuid
from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from app.models.session import SessionCreate, SessionUpdate, SessionResponse
from app.database import db_manager

router = APIRouter(prefix="/api/sessions", tags=["EV Sessions"])


def _compute_session_metrics(doc: dict) -> SessionResponse:
    """Helper to calculate remaining time, minimum required power, and feasibility."""
    now = datetime.now()
    dep = datetime.fromisoformat(doc["departure_time"])
    rem_hours = max(0.01, (dep - now).total_seconds() / 3600.0)
    
    req_kwh = float(doc.get("requested_energy_kwh", 0.0))
    deliv_kwh = float(doc.get("delivered_energy_kwh", 0.0))
    rem_kwh = max(0.0, req_kwh - deliv_kwh)
    
    max_kw = float(doc.get("max_power_kw", 22.0))
    min_required_kw = round(rem_kwh / rem_hours, 2)
    max_possible_kwh = max_kw * rem_hours
    is_achievable = (rem_kwh <= max_possible_kwh + 0.1)

    return SessionResponse(
        id=str(doc.get("id") or doc.get("_id")),
        session_id=doc["session_id"],
        charger_id=doc.get("charger_id", "EVSE-01"),
        arrival_time=doc["arrival_time"],
        departure_time=doc["departure_time"],
        max_power_kw=max_kw,
        requested_energy_kwh=req_kwh,
        delivered_energy_kwh=deliv_kwh,
        initial_soc_pct=doc.get("initial_soc_pct"),
        current_soc_pct=doc.get("current_soc_pct", doc.get("initial_soc_pct")),
        battery_capacity_kwh=doc.get("battery_capacity_kwh"),
        priority=int(doc.get("priority", 3)),
        status=doc.get("status", "active"),
        allocated_power_kw=float(doc.get("allocated_power_kw", 0.0)),
        remaining_hours=round(rem_hours, 2),
        minimum_required_power_kw=min_required_kw,
        is_achievable=is_achievable,
        created_at=doc.get("created_at", now.isoformat())
    )


@router.post("", response_model=SessionResponse, status_code=201)
def create_session(session_in: SessionCreate):
    col = db_manager.get_collection("sessions")
    
    # Check duplicate session_id
    existing = col.find_one({"session_id": session_in.session_id})
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Session with ID '{session_in.session_id}' already exists. IDs must be unique."
        )

    doc = session_in.model_dump()
    doc["id"] = f"SES-{uuid.uuid4().hex[:8].upper()}"
    doc["_id"] = doc["id"]
    doc["delivered_energy_kwh"] = 0.0
    doc["allocated_power_kw"] = min(session_in.max_power_kw, 11.0)  # Initial safe default
    doc["current_soc_pct"] = session_in.initial_soc_pct
    doc["created_at"] = datetime.now().isoformat()
    
    col.insert_one(doc)
    return _compute_session_metrics(doc)


@router.get("", response_model=List[SessionResponse])
def list_sessions(status: Optional[str] = Query(None, description="Filter by status: active, completed, etc.")):
    col = db_manager.get_collection("sessions")
    query = {"status": status} if status else {}
    results = col.find(query)
    
    # If empty on initial startup, populate with 5 realistic active demo sessions
    if not results and (status is None or status == "active"):
        results = _seed_demo_sessions()
        
    return [_compute_session_metrics(d) for d in results]


@router.get("/{id}", response_model=SessionResponse)
def get_session(id: str):
    col = db_manager.get_collection("sessions")
    doc = col.find_one({"session_id": id}) or col.find_one({"id": id}) or col.find_one({"_id": id})
    if not doc:
        raise HTTPException(status_code=404, detail=f"Session '{id}' not found.")
    return _compute_session_metrics(doc)


@router.put("/{id}", response_model=SessionResponse)
def update_session(id: str, update_in: SessionUpdate):
    col = db_manager.get_collection("sessions")
    doc = col.find_one({"session_id": id}) or col.find_one({"id": id}) or col.find_one({"_id": id})
    if not doc:
        raise HTTPException(status_code=404, detail=f"Session '{id}' not found.")
        
    update_data = {k: v for k, v in update_in.model_dump().items() if v is not None}
    if not update_data:
        return _compute_session_metrics(doc)
        
    target_id = doc.get("id") or doc.get("_id")
    col.update_one({"id": target_id}, {"$set": update_data})
    updated = col.find_one({"id": target_id})
    return _compute_session_metrics(updated)


@router.delete("/{id}")
def delete_session(id: str):
    col = db_manager.get_collection("sessions")
    doc = col.find_one({"session_id": id}) or col.find_one({"id": id}) or col.find_one({"_id": id})
    if not doc:
        raise HTTPException(status_code=404, detail=f"Session '{id}' not found.")
        
    target_id = doc.get("id") or doc.get("_id")
    res = col.delete_one({"id": target_id})
    return {"message": f"Session '{id}' deleted successfully.", "deleted_count": getattr(res, "deleted_count", 1)}


def _seed_demo_sessions():
    """Seed 5 realistic active EV charging sessions for immediate demonstration."""
    col = db_manager.get_collection("sessions")
    now = datetime.now()
    demo_sessions = [
        {
            "id": "SES-DEMO-01",
            "_id": "SES-DEMO-01",
            "session_id": "EV-TESLA-302",
            "charger_id": "EVSE-01",
            "arrival_time": (now - timedelta(minutes=45)).isoformat(),
            "departure_time": (now + timedelta(hours=3, minutes=15)).isoformat(),
            "max_power_kw": 22.0,
            "requested_energy_kwh": 48.0,
            "delivered_energy_kwh": 14.5,
            "initial_soc_pct": 24.0,
            "current_soc_pct": 42.0,
            "battery_capacity_kwh": 75.0,
            "priority": 4,
            "status": "active",
            "allocated_power_kw": 18.5,
            "created_at": now.isoformat()
        },
        {
            "id": "SES-DEMO-02",
            "_id": "SES-DEMO-02",
            "session_id": "EV-HYUNDAI-511",
            "charger_id": "EVSE-02",
            "arrival_time": (now - timedelta(minutes=20)).isoformat(),
            "departure_time": (now + timedelta(hours=1, minutes=40)).isoformat(),
            "max_power_kw": 50.0,
            "requested_energy_kwh": 35.0,
            "delivered_energy_kwh": 8.0,
            "initial_soc_pct": 30.0,
            "current_soc_pct": 41.0,
            "battery_capacity_kwh": 77.4,
            "priority": 5,
            "status": "active",
            "allocated_power_kw": 32.0,
            "created_at": now.isoformat()
        },
        {
            "id": "SES-DEMO-03",
            "_id": "SES-DEMO-03",
            "session_id": "EV-NISSAN-109",
            "charger_id": "EVSE-03",
            "arrival_time": (now - timedelta(minutes=80)).isoformat(),
            "departure_time": (now + timedelta(hours=4, minutes=30)).isoformat(),
            "max_power_kw": 11.0,
            "requested_energy_kwh": 28.0,
            "delivered_energy_kwh": 12.0,
            "initial_soc_pct": 45.0,
            "current_soc_pct": 65.0,
            "battery_capacity_kwh": 40.0,
            "priority": 2,
            "status": "active",
            "allocated_power_kw": 7.4,
            "created_at": now.isoformat()
        },
        {
            "id": "SES-DEMO-04",
            "_id": "SES-DEMO-04",
            "session_id": "EV-FORD-883",
            "charger_id": "EVSE-04",
            "arrival_time": (now - timedelta(minutes=15)).isoformat(),
            "departure_time": (now + timedelta(hours=2, minutes=0)).isoformat(),
            "max_power_kw": 22.0,
            "requested_energy_kwh": 30.0,
            "delivered_energy_kwh": 4.0,
            "initial_soc_pct": 20.0,
            "current_soc_pct": 24.5,
            "battery_capacity_kwh": 98.0,
            "priority": 3,
            "status": "active",
            "allocated_power_kw": 16.0,
            "created_at": now.isoformat()
        },
        {
            "id": "SES-DEMO-05",
            "_id": "SES-DEMO-05",
            "session_id": "EV-BMW-420",
            "charger_id": "EVSE-05",
            "arrival_time": (now - timedelta(minutes=5)).isoformat(),
            "departure_time": (now + timedelta(hours=5, minutes=0)).isoformat(),
            "max_power_kw": 11.0,
            "requested_energy_kwh": 20.0,
            "delivered_energy_kwh": 1.0,
            "initial_soc_pct": 55.0,
            "current_soc_pct": 57.0,
            "battery_capacity_kwh": 70.0,
            "priority": 2,
            "status": "active",
            "allocated_power_kw": 6.5,
            "created_at": now.isoformat()
        }
    ]
    for s in demo_sessions:
        col.insert_one(s)
    return demo_sessions
