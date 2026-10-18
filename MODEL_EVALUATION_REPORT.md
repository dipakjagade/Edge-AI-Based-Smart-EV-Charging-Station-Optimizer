# Model Evaluation Report: Edge AI Demand Prediction

## 1. Executive Summary
The demand prediction model is an edge-optimized **RandomForestRegressor** trained to forecast total charging station electrical load in kilowatts (kW). The evaluation was conducted strictly using a **chronological holdout partition** (the first 80% of time-series data for training, and the final 20% strictly as unseen future test data) to prevent temporal data leakage.

## 2. Benchmark Evaluation Metrics

| Metric | Naive Persistence Baseline | Random Forest Regressor | Improvement |
| :--- | :--- | :--- | :--- |
| **Mean Absolute Error (MAE)** | 20.346 kW | **4.903 kW** | **+75.90% Accuracy Gain** |
| **Root Mean Squared Error (RMSE)** | 26.236 kW | **7.106 kW** | **+72.91% Error Reduction** |
| **Coefficient of Determination ($R^2$)** | 0.6510 | **0.9757** | **High Goodness of Fit** |
| **Evaluation Method** | Lagged 1-hour persistence | 100 Trees, Max Depth 15 | Chronological 1,728 samples |

> [!IMPORTANT]
> The Random Forest model achieved a **75.90% reduction in MAE** compared to the naive persistence baseline, demonstrating substantial predictive value over static or simple recency heuristics.

## 3. Top Feature Importances (Gini Impurity)

```
Feature                         Importance Weight (%)
------------------------------------------------------
active_sessions                 [████████████████████] 97.66%
avg_battery_soc                 [█                   ]  0.65%
total_requested_energy_kwh      [█                   ]  0.51%
lagged_demand_24h_kw            [                    ]  0.35%
lagged_demand_1h_kw             [                    ]  0.34%
rolling_mean_3h_kw              [                    ]  0.32%
day_of_week                     [                    ]  0.09%
hour                            [                    ]  0.06%
is_weekend                      [                    ]  0.01%
tariff_rate                     [                    ]  0.01%
```

## 4. Model Persistence & Metadata
- **Artifact Path:** `backend/saved_models/rf_demand_model.joblib`
- **Metadata Path:** `backend/saved_models/model_metadata.json`
- **Hyperparameters:**
  * `n_estimators`: 100
  * `max_depth`: 15
  * `min_samples_split`: 4
  * `min_samples_leaf`: 2
  * `random_state`: 42
- **Ensemble Variance:** Used at inference time across all 100 decision trees to produce real-time 95% Confidence Intervals $[P_{lower}, P_{upper}]$.
