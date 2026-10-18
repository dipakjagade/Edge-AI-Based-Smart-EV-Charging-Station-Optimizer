"""
System Alerts and Edge Health Monitoring Service.
Monitors station transformer capacity, deadline feasibility, model availability,
and database status.
"""

import uuid
from datetime import datetime
from typing import List, Dict, Any
from app.config import settings
from app.models.settings import AlertItem
from app.database import db_manager
from app.services.ml_service import ml_service


class AlertService:
    def __init__(self):
        pass

    def evaluate_system_health(self) -> Dict[str, Any]:
        """Aggregate health indicators for Edge computer."""
        db_health = db_manager.check_health()
        model_loaded = ml_service.is_loaded
        
        health_status = "healthy"
        if not model_loaded:
            health_status = "degraded_model_fallback"
        if db_health["status"] != "connected":
            # Using persistent local storage fallback
            pass

        return {
            "status": health_status,
            "edge_computer": {
                "os": "Edge Linux/Windows MiniPC",
                "mode": "Offline Local Inference",
                "model_loaded": model_loaded,
                "model_version": ml_service.metadata.get("version", "1.0.0"),
                "model_type": ml_service.metadata.get("model_type", "RandomForestRegressor")
            },
            "database": db_health,
            "station": {
                "name": "Antigravity Edge EV Hub #1",
                "capacity_kw": settings.DEFAULT_STATION_CAPACITY_KW,
                "max_chargers": settings.DEFAULT_MAX_CHARGERS
            },
            "timestamp": datetime.now().isoformat()
        }

    def get_active_alerts(self) -> List[AlertItem]:
        """Generate live context-aware alerts based on actual system state."""
        alerts: List[AlertItem] = []
        now = datetime.now().isoformat()

        # 1. AI Model status check
        if not ml_service.is_loaded:
            alerts.append(AlertItem(
                id="ALT-MOD-01",
                severity="warning",
                title="AI Prediction Engine in Fallback Mode",
                message="Trained Random Forest model file not detected on local disk. Conservative capacity heuristics are currently active.",
                source="edge_health",
                timestamp=now,
                resolved=False
            ))

        # 2. Database connection status
        db_health = db_manager.check_health()
        if db_health["status"] != "connected":
            alerts.append(AlertItem(
                id="ALT-DB-01",
                severity="info",
                title="Resilient Local Cache Active",
                message="Operating with local persistent JSON cache. All telemetry and session histories are securely retained locally.",
                source="database",
                timestamp=now,
                resolved=False
            ))

        # 3. Pull persistent alerts logged by optimizer or prediction
        try:
            col = db_manager.get_collection("alerts")
            stored = col.find({"resolved": False})
            for s in stored:
                alerts.append(AlertItem(**s))
        except Exception:
            pass

        return alerts

    def create_alert(self, severity: str, title: str, message: str, source: str) -> AlertItem:
        alt = AlertItem(
            id=f"ALT-{uuid.uuid4().hex[:6].upper()}",
            severity=severity,
            title=title,
            message=message,
            source=source,
            timestamp=datetime.now().isoformat(),
            resolved=False
        )
        try:
            col = db_manager.get_collection("alerts")
            col.insert_one(alt.dict())
        except Exception:
            pass
        return alt


alert_service = AlertService()
