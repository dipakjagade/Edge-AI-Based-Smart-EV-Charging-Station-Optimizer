"""
Demand Prediction Service for Edge AI EV Charging Station.
Loads local Random Forest model, performs offline inference, computes confidence intervals,
and provides a safe fallback when model is unavailable or inputs are degraded.
"""

import os
import json
import uuid
from datetime import datetime
from typing import Dict, Any, Optional
import numpy as np
import pandas as pd
import joblib
from app.config import settings
from app.models.prediction import PredictionRequest, PredictionResponse
from app.database import db_manager

FEATURE_NAMES = [
    "hour",
    "day_of_week",
    "is_weekend",
    "active_sessions",
    "total_requested_energy_kwh",
    "avg_battery_soc",
    "tariff_rate",
    "lagged_demand_1h_kw",
    "lagged_demand_24h_kw",
    "rolling_mean_3h_kw"
]


class MLService:
    def __init__(self):
        self.model = None
        self.metadata = {}
        self.is_loaded = False
        self.load_model()

    def load_model(self):
        """Attempt to load saved joblib model and metadata from disk."""
        if os.path.exists(settings.MODEL_PATH):
            try:
                self.model = joblib.load(settings.MODEL_PATH)
                self.is_loaded = True
                print(f"[+] Loaded Edge AI model successfully from: {settings.MODEL_PATH}")
            except Exception as e:
                self.model = None
                self.is_loaded = False
                print(f"[!] Error loading model file: {e}")
        else:
            self.model = None
            self.is_loaded = False
            print(f"[!] Model file not found at: {settings.MODEL_PATH}. Safe fallback enabled.")

        if os.path.exists(settings.MODEL_METADATA_PATH):
            try:
                with open(settings.MODEL_METADATA_PATH, "r") as f:
                    self.metadata = json.load(f)
            except Exception:
                self.metadata = {}

    def predict_demand(self, req: PredictionRequest) -> PredictionResponse:
        """
        Execute prediction with validation, tree variance confidence intervals,
        and safe conservative fallback.
        """
        is_weekend = req.is_weekend if req.is_weekend is not None else (1 if req.day_of_week >= 5 else 0)
        station_capacity = req.station_capacity_kw or settings.DEFAULT_STATION_CAPACITY_KW
        
        # Estimate lagged defaults if not provided
        est_avg_kw = 12.0
        lagged_1h = req.lagged_demand_1h_kw if req.lagged_demand_1h_kw is not None else min(req.active_sessions * est_avg_kw, station_capacity)
        lagged_24h = req.lagged_demand_24h_kw if req.lagged_demand_24h_kw is not None else lagged_1h
        rolling_3h = req.rolling_mean_3h_kw if req.rolling_mean_3h_kw is not None else lagged_1h
        
        baseline_prediction = float(round(lagged_1h, 2))
        fallback_used = False
        warning = None

        features_dict = {
            "hour": req.hour,
            "day_of_week": req.day_of_week,
            "is_weekend": is_weekend,
            "active_sessions": req.active_sessions,
            "total_requested_energy_kwh": req.total_requested_energy_kwh,
            "avg_battery_soc": req.avg_battery_soc,
            "tariff_rate": req.tariff_rate,
            "lagged_demand_1h_kw": lagged_1h,
            "lagged_demand_24h_kw": lagged_24h,
            "rolling_mean_3h_kw": rolling_3h
        }

        # Check model availability
        if self.is_loaded and self.model is not None:
            try:
                # Prepare single-row DataFrame
                X = pd.DataFrame([features_dict])[FEATURE_NAMES]
                predicted_val = float(self.model.predict(X)[0])
                
                # Compute tree-level standard deviation for confidence interval
                tree_predictions = [tree.predict(X)[0] for tree in self.model.estimators_]
                tree_std = float(np.std(tree_predictions))
                lower_kw = max(0.0, predicted_val - 1.96 * tree_std)
                upper_kw = predicted_val + 1.96 * tree_std
            except Exception as e:
                # Safe conservative fallback
                fallback_used = True
                warning = f"Prediction failed with error ({e}), applied conservative capacity fallback."
                predicted_val = min(req.active_sessions * 11.5, station_capacity)
                lower_kw = max(0.0, predicted_val * 0.85)
                upper_kw = min(station_capacity, predicted_val * 1.15)
        else:
            # Safe conservative heuristic when model file is not present
            fallback_used = True
            warning = "AI Model file is not present on edge disk. Operating in safe conservative fallback mode."
            predicted_val = min(req.active_sessions * 11.5, station_capacity)
            lower_kw = max(0.0, predicted_val * 0.85)
            upper_kw = min(station_capacity, predicted_val * 1.15)

        # Enforce non-negative and zero-session zero-demand condition
        if req.active_sessions == 0:
            predicted_val = 0.0
            lower_kw = 0.0
            upper_kw = 0.0
        else:
            predicted_val = max(0.0, round(predicted_val, 2))
            lower_kw = max(0.0, round(lower_kw, 2))
            upper_kw = max(0.0, round(upper_kw, 2))

        capacity_exceeded = predicted_val > station_capacity
        headroom_kw = round(station_capacity - predicted_val, 2)
        pred_id = f"PRED-{uuid.uuid4().hex[:8].upper()}"
        now_iso = datetime.now().isoformat()

        response = PredictionResponse(
            id=pred_id,
            predicted_demand_kw=predicted_val,
            confidence_interval={"lower_kw": lower_kw, "upper_kw": upper_kw},
            baseline_prediction_kw=baseline_prediction,
            model_version=self.metadata.get("version", "1.0.0-fallback"),
            model_type="RandomForestRegressor" if not fallback_used else "ConservativeHeuristicFallback",
            fallback_used=fallback_used,
            warning=warning,
            input_features=features_dict,
            capacity_exceeded=capacity_exceeded,
            capacity_headroom_kw=headroom_kw,
            timestamp=now_iso
        )

        # Persist to database/local cache
        try:
            col = db_manager.get_collection("predictions")
            col.insert_one(response.model_dump())
        except Exception as e:
            print(f"[*] Prediction persistence note: {e}")

        return response


ml_service = MLService()
