"""
Model Training and Evaluation API Routes.
"""

import os
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, BackgroundTasks, Query
from app.config import settings
from app.services.ml_service import ml_service
from ml.train_model import train_demand_model

router = APIRouter(prefix="/api/models", tags=["Model Training & Evaluation"])

# Global training state
training_state = {
    "is_training": False,
    "last_run_timestamp": None,
    "last_status": "idle",
    "error_message": None
}


def _run_training_job(csv_path: str, n_estimators: int, max_depth: int):
    global training_state
    training_state["is_training"] = True
    training_state["last_status"] = "training"
    training_state["error_message"] = None
    try:
        metadata = train_demand_model(
            csv_path=csv_path,
            model_output_dir=settings.MODEL_DIR,
            n_estimators=n_estimators,
            max_depth=max_depth
        )
        ml_service.load_model()
        training_state["last_status"] = "completed"
        training_state["last_run_timestamp"] = metadata.get("trained_at")
    except Exception as e:
        training_state["last_status"] = "failed"
        training_state["error_message"] = str(e)
    finally:
        training_state["is_training"] = False


@router.post("/train")
def train_model(
    background_tasks: BackgroundTasks,
    estimators: int = Query(50, ge=10, le=200, description="Number of trees"),
    depth: int = Query(12, ge=4, le=25, description="Tree max depth"),
    csv_file: str = Query("synthetic_ev_charging_data.csv", description="CSV file in data dir")
):
    """Trigger Edge AI Random Forest training job in the background."""
    global training_state
    if training_state["is_training"]:
        raise HTTPException(status_code=409, detail="A model training job is already in progress.")

    csv_path = os.path.join(settings.DATA_DIR, csv_file)
    if not os.path.exists(csv_path):
        raise HTTPException(status_code=404, detail=f"Dataset '{csv_file}' not found in data directory.")

    background_tasks.add_task(_run_training_job, csv_path, estimators, depth)
    return {
        "message": "Model training job initiated in background.",
        "parameters": {
            "estimators": estimators,
            "max_depth": depth,
            "dataset": csv_file
        },
        "status": "training"
    }


@router.get("/status")
def get_model_status() -> Dict[str, Any]:
    """Returns training progress and loaded model state."""
    return {
        "model_loaded": ml_service.is_loaded,
        "is_training": training_state["is_training"],
        "last_status": training_state["last_status"],
        "error_message": training_state["error_message"],
        "model_path": settings.MODEL_PATH,
        "model_exists_on_disk": os.path.exists(settings.MODEL_PATH),
        "metadata_exists_on_disk": os.path.exists(settings.MODEL_METADATA_PATH),
        "active_version": ml_service.metadata.get("version", "1.0.0"),
        "trained_at": ml_service.metadata.get("trained_at")
    }


@router.get("/metrics")
def get_model_metrics() -> Dict[str, Any]:
    """Returns MAE, RMSE, feature importances, and sample evaluation chart data."""
    if not ml_service.metadata:
        ml_service.load_model()
        
    if not ml_service.metadata:
        raise HTTPException(
            status_code=404,
            detail="Model metadata not found. Please train the model first."
        )
        
    return ml_service.metadata
