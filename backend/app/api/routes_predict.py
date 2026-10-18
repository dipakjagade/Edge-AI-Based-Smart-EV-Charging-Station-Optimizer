"""
Demand Prediction API Routes.
"""

from typing import List
from fastapi import APIRouter, HTTPException
from app.models.prediction import PredictionRequest, PredictionResponse
from app.services.ml_service import ml_service
from app.database import db_manager

router = APIRouter(prefix="/api", tags=["Demand Prediction"])


@router.post("/predict", response_model=PredictionResponse)
def run_prediction(req: PredictionRequest):
    """
    Execute AI demand prediction for the EV charging station.
    Runs locally on edge computer using loaded Random Forest model.
    Falls back gracefully to safe capacity heuristic if model is absent.
    """
    try:
        response = ml_service.predict_demand(req)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction error: {str(e)}")


@router.get("/predictions", response_model=List[PredictionResponse])
def get_prediction_history(limit: int = 50):
    col = db_manager.get_collection("predictions")
    results = col.find()
    # Return recent first
    reversed_results = list(reversed(results))[:limit]
    return [PredictionResponse(**r) for r in reversed_results]


@router.get("/predictions/{id}", response_model=PredictionResponse)
def get_single_prediction(id: str):
    col = db_manager.get_collection("predictions")
    doc = col.find_one({"id": id}) or col.find_one({"_id": id})
    if not doc:
        raise HTTPException(status_code=404, detail=f"Prediction record '{id}' not found.")
    return PredictionResponse(**doc)
