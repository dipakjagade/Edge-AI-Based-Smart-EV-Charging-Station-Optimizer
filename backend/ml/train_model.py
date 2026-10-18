"""
Model Training and Evaluation Pipeline for Edge AI EV Demand Prediction.
Uses Scikit-learn RandomForestRegressor with strict chronological holdout validation.
Calculates MAE, RMSE, and compares against a baseline predictor.
"""

import os
import json
import argparse
from datetime import datetime
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import joblib

FEATURE_COLUMNS = [
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

TARGET_COLUMN = "station_demand_kw"


def load_and_preprocess_data(csv_path: str):
    """Load CSV, validate required columns, and sort chronologically."""
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Dataset not found at: {csv_path}")
        
    df = pd.read_csv(csv_path)
    if "timestamp" in df.columns:
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df = df.sort_values("timestamp").reset_index(drop=True)
    
    # Check features
    missing = [c for c in FEATURE_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"Dataset is missing required features: {missing}")
        
    if TARGET_COLUMN not in df.columns:
        raise ValueError(f"Target column '{TARGET_COLUMN}' missing from dataset.")
        
    # Drop rows with NaN in features or target
    df_clean = df.dropna(subset=FEATURE_COLUMNS + [TARGET_COLUMN]).copy()
    return df_clean


def train_demand_model(
    csv_path: str = "backend/data/synthetic_ev_charging_data.csv",
    model_output_dir: str = "backend/saved_models",
    n_estimators: int = 100,
    max_depth: int = 15,
    test_ratio: float = 0.20,
    random_seed: int = 42
):
    """
    Train Random Forest regressor with chronological train/test split.
    Evaluates against Persistence Baseline.
    Persists model artifact and metadata JSON.
    """
    os.makedirs(model_output_dir, exist_ok=True)
    df = load_and_preprocess_data(csv_path)
    
    # Strict chronological split (No shuffling!)
    split_idx = int(len(df) * (1.0 - test_ratio))
    train_df = df.iloc[:split_idx]
    test_df = df.iloc[split_idx:]
    
    X_train = train_df[FEATURE_COLUMNS]
    y_train = train_df[TARGET_COLUMN]
    X_test = test_df[FEATURE_COLUMNS]
    y_test = test_df[TARGET_COLUMN]
    
    print(f"[*] Training dataset size: {len(X_train)} samples")
    print(f"[*] Testing dataset size:  {len(X_test)} samples (Chronological Holdout)")
    
    # 1. Baseline Model: Lagged 1-hour Demand Persistence
    baseline_preds = X_test["lagged_demand_1h_kw"]
    baseline_mae = float(mean_absolute_error(y_test, baseline_preds))
    baseline_rmse = float(np.sqrt(mean_squared_error(y_test, baseline_preds)))
    
    # 2. Random Forest Model
    print("[*] Training RandomForestRegressor...")
    model = RandomForestRegressor(
        n_estimators=n_estimators,
        max_depth=max_depth,
        min_samples_split=4,
        min_samples_leaf=2,
        random_state=random_seed,
        n_jobs=-1
    )
    model.fit(X_train, y_train)
    
    # 3. Model Inference & Evaluation
    preds = model.predict(X_test)
    rf_mae = float(mean_absolute_error(y_test, preds))
    rf_rmse = float(np.sqrt(mean_squared_error(y_test, preds)))
    rf_r2 = float(r2_score(y_test, preds))
    
    # Feature importances
    importances = {feat: round(float(imp), 4) for feat, imp in zip(FEATURE_COLUMNS, model.feature_importances_)}
    sorted_importances = dict(sorted(importances.items(), key=lambda item: item[1], reverse=True))
    
    print("\n" + "="*50)
    print("MODEL EVALUATION RESULTS (Chronological Holdout)")
    print("="*50)
    print(f"Naive Baseline MAE:     {baseline_mae:.3f} kW | RMSE: {baseline_rmse:.3f} kW")
    print(f"Random Forest MAE:      {rf_mae:.3f} kW | RMSE: {rf_rmse:.3f} kW")
    print(f"R-squared Score (R2):   {rf_r2:.4f}")
    improvement = ((baseline_mae - rf_mae) / baseline_mae) * 100.0
    print(f"Accuracy Improvement over Baseline: {improvement:.2f}%")
    print("Feature Importances:")
    for f, imp in sorted_importances.items():
        print(f"  - {f:30s}: {imp:.4f}")
    print("="*50 + "\n")
    
    # 4. Save Model Artifact
    model_path = os.path.join(model_output_dir, "rf_demand_model.joblib")
    joblib.dump(model, model_path)
    print(f"[+] Model saved to: {model_path}")
    
    # 5. Extract Sample Test Comparisons (first 100 points of test set for visualization)
    sample_size = min(120, len(test_df))
    sample_timestamps = [str(t) for t in test_df["timestamp"].iloc[:sample_size]] if "timestamp" in test_df else [str(i) for i in range(sample_size)]
    sample_actual = [round(float(v), 2) for v in y_test.iloc[:sample_size]]
    sample_predicted = [round(float(v), 2) for v in preds[:sample_size]]
    sample_baseline = [round(float(v), 2) for v in baseline_preds.iloc[:sample_size]]
    
    # 6. Save Metadata JSON
    metadata = {
        "model_type": "RandomForestRegressor",
        "version": "1.0.0",
        "trained_at": datetime.now().isoformat(),
        "dataset_source": os.path.basename(csv_path),
        "total_samples": len(df),
        "train_samples": len(X_train),
        "test_samples": len(X_test),
        "test_ratio": test_ratio,
        "features": FEATURE_COLUMNS,
        "target": TARGET_COLUMN,
        "hyperparameters": {
            "n_estimators": n_estimators,
            "max_depth": max_depth,
            "min_samples_split": 4,
            "min_samples_leaf": 2,
            "random_state": random_seed
        },
        "metrics": {
            "rf_mae_kw": round(rf_mae, 3),
            "rf_rmse_kw": round(rf_rmse, 3),
            "rf_r2": round(rf_r2, 4),
            "baseline_mae_kw": round(baseline_mae, 3),
            "baseline_rmse_kw": round(baseline_rmse, 3),
            "mae_improvement_pct": round(improvement, 2)
        },
        "feature_importances": sorted_importances,
        "sample_eval_chart": {
            "timestamps": sample_timestamps,
            "actual": sample_actual,
            "predicted": sample_predicted,
            "baseline": sample_baseline
        }
    }
    
    meta_path = os.path.join(model_output_dir, "model_metadata.json")
    with open(meta_path, "w") as f:
        json.dump(metadata, f, indent=2)
    print(f"[+] Model metadata and evaluation metrics saved to: {meta_path}")
    
    return metadata


def main():
    parser = argparse.ArgumentParser(description="Train Random Forest demand prediction model.")
    parser.add_argument("--csv", type=str, default="backend/data/synthetic_ev_charging_data.csv", help="Path to input CSV")
    parser.add_argument("--output-dir", type=str, default="backend/saved_models", help="Output directory for model")
    parser.add_argument("--estimators", type=int, default=100, help="Number of trees in RF")
    parser.add_argument("--depth", type=int, default=15, help="Max depth of trees")
    args = parser.parse_args()
    
    train_demand_model(
        csv_path=args.csv,
        model_output_dir=args.output_dir,
        n_estimators=args.estimators,
        max_depth=args.depth
    )


if __name__ == "__main__":
    main()
