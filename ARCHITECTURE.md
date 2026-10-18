# System Architecture: Edge AI Based Smart EV Charging Station Optimizer

## 1. High-Level Architectural Diagram

```
+---------------------------------------------------------------------------------------------------+
|                                      EDGE COMPUTER ENCLOSURE                                      |
|                       (Raspberry Pi 5 8GB / Industrial Mini-PC / Edge Server)                     |
|                                                                                                   |
|  +---------------------------------------------------------------------------------------------+  |
|  |                            Vite + React SPA Dashboard (Port 3000)                           |  |
|  |  +-------------------+  +-------------------+  +-------------------+  +------------------+  |  |
|  |  | Station Overview  |  | EV Session CRUD   |  | Demand Predictor  |  | Power Optimizer  |  |  |
|  |  +-------------------+  +-------------------+  +-------------------+  +------------------+  |  |
|  |  +-------------------+  +-------------------+  +-------------------+  +------------------+  |  |
|  |  | Dataset Audit     |  | Model Training    |  | Cost Analytics    |  | Alerts & Health  |  |  |
|  |  +-------------------+  +-------------------+  +-------------------+  +------------------+  |  |
|  +-----------------------------------------------+---------------------------------------------+  |
|                                                  | HTTP / JSON REST APIs                          |
|                                                  v                                                |
|  +---------------------------------------------------------------------------------------------+  |
|  |                              FastAPI Edge Backend (Port 8000)                               |  |
|  |  - Lifespan Startup: Connect DB, Load Local Joblib Model                                    |  |
|  |  - Middleware: CORS, Request Timing, Pydantic Schema Validation                             |  |
|  |  - Routers: /health, /api/dashboard, /api/sessions, /api/predict, /api/optimize,            |  |
|  |             /api/datasets, /api/models, /api/analytics, /api/alerts, /api/settings          |  |
|  +---------------+-------------------------------+-----------------------------+---------------+  |
|                  |                               |                             |                  |
|                  v                               v                             v                  |
|  +-------------------------------+ +-----------------------------+ +---------------------------+  |
|  |     Demand Prediction Engine  | |   Smart Power Optimizer     | | Dataset & Tariff Services |  |
|  | - Scikit-learn Random Forest  | | - Deterministic Water-      | | - CSV Parser & Imputer    |  |
|  | - 10-Tree Ensemble Variance   | |   Filling (Urgency & Weight)| | - ACN-Data Schema Mapper  |  |
|  | - 95% Confidence Intervals    | | - 15-min Time Slot LP       | | - Data Quality Scoring    |  |
|  | - Safe Capacity Heuristic     | | - Transformer Headroom Cap  | | - TOU Tariff Analytics    |  |
|  |   Fallback on Missing Model   | | - Bottleneck Diagnostics    | | - 3-Way Policy Benchmark  |  |
|  +---------------+---------------+ +--------------+--------------+ +-------------+-------------+  |
|                  |                                |                             |                 |
|                  +--------------------------------+-----------------------------+                 |
|                                                   |                                               |
|                                                   v                                               |
|  +---------------------------------------------------------------------------------------------+  |
|  |                                  Persistence & Cache Layer                                  |  |
|  |  - Primary: MongoDB (PyMongo / Motor) with collections: sessions, predictions,              |  |
|  |             optimizations, datasets, alerts, settings                                       |  |
|  |  - Resilient Local Fallback: Transparent file-backed JSON store in data/db_fallback/         |  |
|  |    (Guarantees 100% functionality and zero data loss even without network/MongoDB)          |  |
|  +---------------------------------------------------------------------------------------------+  |
+---------------------------------------------------------------------------------------------------+
```

## 2. Core Functional Modules

### 2.1 Dashboard & Telemetry Visualization
- Aggregates live station capacity, active sessions, transformer load %, and electricity cost rates.
- Recharts AreaChart displays the 24-hour diurnal demand profile against the 150 kW hard transformer capacity ceiling.

### 2.2 EV Session Management (CRUD)
- Manages simulated EV sessions with parameters: vehicle ID, charger stall ID, arrival time, departure deadline, battery SOC (%), requested energy (kWh), already delivered energy, priority weight (1-5), and connection status.
- Strict Pydantic validators guarantee non-negative values and chronological validity (departure > arrival).

### 2.3 Edge AI Demand Prediction Service
- Scikit-learn `RandomForestRegressor` persisted in `backend/saved_models/rf_demand_model.joblib`.
- Evaluates 10 input features: `hour`, `day_of_week`, `is_weekend`, `active_sessions`, `total_requested_energy_kwh`, `avg_battery_soc`, `tariff_rate`, `lagged_demand_1h_kw`, `lagged_demand_24h_kw`, `rolling_mean_3h_kw`.
- Calculates tree variance across the ensemble to output a 95% confidence interval `[lower_kw, upper_kw]`.
- Implements a conservative capacity fallback heuristic when the model is absent or inputs are degraded.

### 2.4 Constrained Smart Charging Power Optimizer
- **Mode 1: Weighted Water-Filling Allocation**:
  * $0 \le P_i \le \min(P_{max, i}, P_{needed, i})$
  * $\sum P_i \le P_{station\_max}$ (150 kW)
  * Priority and urgency: $U_i = E_{rem, i} / \Delta t_{rem, i}$; $W_i = \text{priority}_i \times \max(0.5, U_i)$
  * Redistribution: Iteratively locks saturated chargers and redistributes surplus transformer power to unsatisfied vehicles.
  * Infeasibility detection: Distinguishes between physical charger hardware bottlenecks vs station transformer congestion.
- **Mode 2: Advanced 15-Minute Multi-Period Scheduling**:
  * Discretizes charging horizon into 15-minute time slots.
  * Solves cost-minimizing power allocation according to Time-of-Use tariffs ($0.12 off-peak, $0.20 mid-peak, $0.35 on-peak).

### 2.5 Resilient Dual-Layer Persistence
- Connects to MongoDB `smart_ev_charging_db` with a 1500ms timeout on startup.
- If MongoDB is unreachable, it automatically activates the file-backed JSON store in `backend/data/db_fallback/`.
