"""
System Alerts and Settings API Routes.
"""

from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException
from app.models.settings import AlertItem, StationSettings
from app.services.alert_service import alert_service
from app.config import settings
from app.database import db_manager

router = APIRouter(prefix="/api", tags=["Alerts & Settings"])


# ALERTS ROUTES
@router.get("/alerts", response_model=List[AlertItem])
def get_alerts():
    """Retrieve all active system alerts and warnings."""
    return alert_service.get_active_alerts()


@router.post("/alerts/{id}/resolve")
def resolve_alert(id: str):
    """Mark an alert as resolved."""
    col = db_manager.get_collection("alerts")
    res = col.update_one({"id": id}, {"$set": {"resolved": True}})
    return {"message": f"Alert '{id}' marked as resolved.", "modified": getattr(res, "modified_count", 1)}


# SETTINGS ROUTES
@router.get("/settings", response_model=StationSettings)
def get_station_settings():
    col = db_manager.get_collection("settings")
    doc = col.find_one({"type": "station_config"})
    if doc:
        return StationSettings(**doc)
    return StationSettings(
        station_name="Antigravity Edge EV Hub #1",
        station_power_limit_kw=settings.DEFAULT_STATION_CAPACITY_KW,
        total_chargers=settings.DEFAULT_MAX_CHARGERS,
        default_charger_limit_kw=settings.DEFAULT_CHARGER_MAX_KW
    )


@router.post("/settings", response_model=StationSettings)
def update_station_settings(new_settings: StationSettings):
    col = db_manager.get_collection("settings")
    doc = new_settings.dict()
    doc["type"] = "station_config"
    col.update_one({"type": "station_config"}, {"$set": doc})
    
    # Update running settings
    settings.DEFAULT_STATION_CAPACITY_KW = new_settings.station_power_limit_kw
    settings.DEFAULT_MAX_CHARGERS = new_settings.total_chargers
    settings.DEFAULT_CHARGER_MAX_KW = new_settings.default_charger_limit_kw
    
    return new_settings
