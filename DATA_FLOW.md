# Data Flow Specification: Edge AI Based Smart EV Charging Station Optimizer

## 1. End-to-End Data Pipeline

```
[Raw CSV Upload / Simulated Telemetry]
                 |
                 v
   [Data Ingestion & Quality Audit]
     - Missing value imputation
     - Timestamp monotonicity checks
     - Anomaly / Negative power filtering
     - Schema mapping (ACN-Data adapter)
                 |
                 v
   [Chronological Feature Engineering]
     - 1-hour lagged demand (kw)
     - 24-hour lagged demand (kw)
     - 3-hour rolling mean demand (kw)
     - Time-of-use tariff tagging ($/kWh)
                 |
                 +--------------------------------------+
                 |                                      |
                 v                                      v
     [Model Training Pipeline]              [Real-time Inference Pipeline]
     - 80% Chronological Train              - Loaded Random Forest Weights
     - 20% Chronological Holdout            - Feature alignment & validation
     - RandomForestRegressor fit            - Tree ensemble variance calculation
     - MAE, RMSE, R2 vs Baseline            - Output: Forecast Demand & 95% Band
     - Persist joblib + metadata JSON                   |
                                                        v
                                         [Constrained Power Optimizer]
                                           - Read active EV sessions
                                           - Compute urgency & deadline rates
                                           - Water-filling allocation
                                           - Check station transformer limit
                                           - Output allocated kW per vehicle
                                                        |
                                                        v
                                         [Persistence & Monitoring]
                                           - MongoDB / JSON Cache update
                                           - State-based alert generation
                                           - React Dashboard WebSocket/REST
```

## 2. Machine Learning Feature Pipeline

| Feature Name | Type | Range / Unit | Source / Definition |
| :--- | :--- | :--- | :--- |
| `hour` | Integer | 0 &ndash; 23 | Time of day from session timestamp |
| `day_of_week` | Integer | 0 &ndash; 6 | Day of week (0 = Monday, 6 = Sunday) |
| `is_weekend` | Binary | 0 or 1 | 1 if Saturday or Sunday |
| `active_sessions` | Integer | 0 &ndash; 10 | Concurrent vehicles plugged into EVSE stalls |
| `total_requested_energy_kwh` | Float | 0.0 &ndash; 500.0 kWh | Aggregate unserved energy requested by plugged EVs |
| `avg_battery_soc` | Float | 0.0 &ndash; 100.0 % | Average incoming battery state of charge |
| `tariff_rate` | Float | 0.12 &ndash; 0.35 $/kWh | Utility Time-of-Use electricity rate |
| `lagged_demand_1h_kw` | Float | 0.0 &ndash; 150.0 kW | Actual station power consumption 4 intervals (1h) prior |
| `lagged_demand_24h_kw` | Float | 0.0 &ndash; 150.0 kW | Actual station power consumption 96 intervals (24h) prior |
| `rolling_mean_3h_kw` | Float | 0.0 &ndash; 150.0 kW | Rolling 12-interval (3h) mean station demand |
| **`station_demand_kw` (TARGET)** | Float | 0.0 &ndash; 150.0 kW | Net aggregate electrical power draw of the station |

> [!NOTE]
> All lag and rolling features are created strictly forward in time (`shift(1)` or higher) to prevent temporal data leakage. No future information is ever leaked into historical rows.
