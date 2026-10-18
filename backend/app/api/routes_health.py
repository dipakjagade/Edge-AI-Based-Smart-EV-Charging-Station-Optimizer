"""
Health Check and Dashboard Summary API Routes.
"""

from datetime import datetime
from fastapi import APIRouter
from app.config import settings
from app.database import db_manager
from app.services.alert_service import alert_service
from app.services.ml_service import ml_service

router = APIRouter()


@router.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "edge_mode": settings.EDGE_MODE,
        "database": db_manager.check_health(),
        "model_loaded": ml_service.is_loaded,
        "timestamp": datetime.now().isoformat()
    }


@router.get("/api/dashboard/summary")
def get_dashboard_summary():
    """
    Returns aggregated live station status for the main React dashboard.
    Uses real database collections and active sessions.
    """
    sessions_col = db_manager.get_collection("sessions")
    active_sessions = sessions_col.find({"status": "active"})
    active_count = len(active_sessions)
    
    # Calculate allocated power from active sessions
    total_allocated_kw = sum(s.get("allocated_power_kw", 0.0) for s in active_sessions)
    total_requested_kwh = sum(s.get("requested_energy_kwh", 0.0) for s in active_sessions)
    total_delivered_kwh = sum(s.get("delivered_energy_kwh", 0.0) for s in active_sessions)
    
    station_capacity = settings.DEFAULT_STATION_CAPACITY_KW
    remaining_capacity = max(0.0, round(station_capacity - total_allocated_kw, 2))
    
    # Recent predictions
    pred_col = db_manager.get_collection("predictions")
    recent_preds = pred_col.find()
    last_pred = recent_preds[-1] if recent_preds else None
    predicted_demand_kw = last_pred.get("predicted_demand_kw", 0.0) if last_pred else round(active_count * 11.5, 2)
    
    # Recent alerts
    alerts = alert_service.get_active_alerts()
    
    # Current electricity tariff ($/kWh) based on current hour
    current_hour = datetime.now().hour
    if 22 <= current_hour or current_hour < 6:
        tariff = 0.12
        tariff_label = "Off-Peak ($0.12/kWh)"
    elif 14 <= current_hour < 20:
        tariff = 0.35
        tariff_label = "On-Peak ($0.35/kWh)"
    else:
        tariff = 0.20
        tariff_label = "Mid-Peak ($0.20/kWh)"
        
    est_hourly_cost = round(total_allocated_kw * tariff, 2)

    return {
        "demo_mode": settings.DEMO_MODE,
        "edge_mode": settings.EDGE_MODE,
        "station_name": "Antigravity Edge EV Hub #1",
        "station_capacity_kw": station_capacity,
        "allocated_power_kw": round(total_allocated_kw, 2),
        "remaining_capacity_kw": remaining_capacity,
        "utilization_pct": round((total_allocated_kw / max(1.0, station_capacity)) * 100.0, 1),
        "active_sessions_count": active_count,
        "total_requested_energy_kwh": round(total_requested_kwh, 2),
        "total_delivered_energy_kwh": round(total_delivered_kwh, 2),
        "predicted_demand_kw": round(predicted_demand_kw, 2),
        "capacity_warning": (predicted_demand_kw > station_capacity) or (total_allocated_kw > station_capacity),
        "current_tariff": tariff_label,
        "estimated_hourly_cost_usd": est_hourly_cost,
        "active_alerts_count": len(alerts),
        "alerts_preview": alerts[:3],
        "database_status": db_manager.check_health()["status"],
        "model_status": "Loaded" if ml_service.is_loaded else "Fallback Mode",
        "timestamp": datetime.now().isoformat()
    }
