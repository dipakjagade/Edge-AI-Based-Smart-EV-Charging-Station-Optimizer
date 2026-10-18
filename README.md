# Edge AI Based Smart EV Charging Station Optimizer

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com/)
[![React 18](https://img.shields.io/badge/React-18.3+-61DAFB.svg)](https://reactjs.org/)
[![Vite](https://img.shields.io/badge/Vite-5.4+-646CFF.svg)](https://vitejs.dev/)
[![Scikit-Learn](https://img.shields.io/badge/scikit--learn-1.5+-F7931E.svg)](https://scikit-learn.org/)
[![Tests](https://img.shields.io/badge/pytest-19%20passed-brightgreen.svg)](https://docs.pytest.org/)

An enterprise-grade, edge-deployable software platform that predicts electric vehicle charging demand and dynamically optimizes electrical power distribution across concurrent EV charging stalls.

Designed for edge hardware (Raspberry Pi 5, industrial Mini-PCs), this system operates **100% offline without cloud AI API dependencies**, preventing transformer overloads and shaving peak electrical demand charges using constrained mathematical optimization.

---

## Key Features

1. **Edge AI Demand Forecasting:**
   - Local Scikit-learn **Random Forest Regressor** trained on chronological charging telemetry.
   - Outputs demand forecasts in kW alongside 95% Confidence Intervals computed across tree ensemble variance.
   - **75.90% accuracy improvement** over naive persistence baselines.
   - Built-in safe conservative capacity fallback when model files are absent or inputs degraded.

2. **Smart Power Optimization Engine:**
   - **Weighted Water-Filling Algorithm:** Dynamically balances station transformer capacity limits (e.g. 150 kW) with individual EVSE limits (e.g. 22 kW), urgency metrics ($E_{rem} / \Delta t$), and driver priorities (P1&ndash;P5).
   - **Advanced 15-Minute Time-Slot Scheduling:** Solves multi-period power profiles to align charging with low-cost off-peak Time-of-Use tariffs ($0.12/kWh vs $0.35/kWh).
   - **Bottleneck Diagnostics:** Explicitly detects and explains whether infeasibilities are caused by physical charger limits or transformer capacity constraints.

3. **Resilient Dual-Layer Persistence:**
   - Seamlessly integrates with **MongoDB** (`mongodb://localhost:27017`).
   - Includes transparent file-backed JSON persistence fallback in `backend/data/db_fallback/` ensuring zero data loss even in isolated environments.

4. **Modern 10-Page React Dashboard:**
   - **Station Overview:** Real-time metrics, transformer utilization, and 24h diurnal demand vs capacity chart.
   - **EV Session Management:** Full CRUD with input validation, remaining time, and deadline feasibility.
   - **Demand Prediction Workstation:** Interactive parameter sliders, live inference, and 95% confidence bands.
   - **Smart Charging Optimizer:** Power allocation table, stacked 15-min schedule chart, and peak shaving stats.
   - **Dataset Ingestion & Quality Audit:** CSV upload, ACN-Data format adapter, and quality scoring (0&ndash;100%).
   - **Model Training & Evaluation:** Retraining controls, chronological actual vs predicted chart, and feature importances.
   - **Cost & Energy Analytics:** Time-of-Use tariff comparison and 3-way strategy financial audit.
   - **Alerts & Diagnostics:** Real-time state-based health monitoring and overload warnings.
   - **Application Settings:** Transformer capacity, charger limits, and TOU tariff configuration.
   - **Interactive Documentation:** Architecture diagrams, math explanations, and Swagger API links.

---

## Project Structure

```
.
├── backend/
│   ├── app/
│   │   ├── main.py                     # FastAPI application setup, CORS, lifespan, routes
│   │   ├── config.py                   # App configuration & environment settings
│   │   ├── database.py                 # Resilient MongoDB client + local JSON fallback
│   │   ├── models/                     # Pydantic schemas (session, prediction, optimization, dataset, settings)
│   │   ├── services/                   # Business logic (ml_service, optimizer_service, tariff_service, alert_service)
│   │   └── api/                        # REST endpoint routers
│   ├── ml/
│   │   ├── generate_synthetic_data.py  # Realistic 90-day EV station telemetry generator
│   │   └── train_model.py              # Chronological train/eval pipeline & joblib saver
│   ├── data/                           # Benchmarks (synthetic CSV, sample ACN-Data, uploads)
│   ├── saved_models/                   # Persisted Random Forest joblib model & metadata JSON
│   ├── tests/                          # 19 automated pytest unit & integration tests
│   ├── requirements.txt
│   └── run_server.py                   # Server startup runner
├── frontend/
│   ├── src/
│   │   ├── components/                 # Sidebar, Header, MetricCard, StatusBadge, Modal
│   │   ├── pages/                      # 10 complete application pages
│   │   ├── services/api.js             # Axios client with error handling
│   │   ├── App.jsx
│   │   └── index.css                   # Modern dark-mode glassmorphism design system
│   ├── package.json
│   └── vite.config.js
├── docker-compose.yml
├── Dockerfile.backend
├── Dockerfile.frontend
├── ARCHITECTURE.md
├── DATA_FLOW.md
├── MODEL_EVALUATION_REPORT.md
├── TEST_REPORT.md
├── EDGE_DEPLOYMENT_GUIDE.md
├── pytest.ini
├── .env.example
└── .gitignore
```

---

## Quick Start Guide

### 1. Prerequisites
- Python 3.11+
- Node.js 18+ and npm
- (Optional) MongoDB running locally or via Docker

### 2. Backend Setup & AI Training

```bash
# 1. Install backend dependencies
pip install -r backend/requirements.txt

# 2. Generate 90-day synthetic telemetry benchmark (8,640 intervals)
python backend/ml/generate_synthetic_data.py --days 90

# 3. Train the Edge AI Random Forest model
python backend/ml/train_model.py

# 4. Start the FastAPI backend
python backend/run_server.py
```
Backend API will be running at: `http://localhost:8000` (Swagger UI at `http://localhost:8000/docs`).

### 3. Frontend Dashboard Setup

In a new terminal window:

```bash
cd frontend
npm install
npm run dev
```
Open your browser at: `http://localhost:3000`

---

## Running Automated Tests

Run the comprehensive pytest suite covering API endpoints, dataset validation, ML inference, optimizer constraints, and tariff calculations:

```bash
python -m pytest backend/tests -v
```

All 19 tests will execute and pass:
```
backend/tests/test_api_endpoints.py::test_health_check_endpoint PASSED
backend/tests/test_api_endpoints.py::test_dashboard_summary_endpoint PASSED
backend/tests/test_api_endpoints.py::test_sessions_crud_flow PASSED
backend/tests/test_api_endpoints.py::test_prediction_endpoint PASSED
backend/tests/test_api_endpoints.py::test_optimization_endpoint PASSED
backend/tests/test_api_endpoints.py::test_analytics_endpoints PASSED
backend/tests/test_dataset_validation.py::test_synthetic_data_generation PASSED
backend/tests/test_dataset_validation.py::test_sample_acn_dataset_properties PASSED
backend/tests/test_dataset_validation.py::test_dataset_quality_inspection PASSED
backend/tests/test_model_training_inference.py::test_model_loaded_and_predicts PASSED
backend/tests/test_model_training_inference.py::test_zero_sessions_zero_demand PASSED
backend/tests/test_model_training_inference.py::test_safe_conservative_fallback_mode PASSED
backend/tests/test_optimizer.py::test_station_capacity_and_charger_limits PASSED
backend/tests/test_optimizer.py::test_zero_energy_receives_zero_power PASSED
backend/tests/test_optimizer.py::test_reject_duplicate_session_ids PASSED
backend/tests/test_optimizer.py::test_infeasible_deadline_detection PASSED
backend/tests/test_optimizer.py::test_advanced_15min_scheduler PASSED
backend/tests/test_tariffs_cost.py::test_time_of_use_tariff_schedule PASSED
backend/tests/test_tariffs_cost.py::test_cost_comparison_analytics PASSED

====================== 19 passed in 5.28s =======================
```

---

## Docker Deployment

To spin up the entire multi-container stack (MongoDB, Backend, and Frontend Nginx) with one command:

```bash
docker-compose up --build
```
- Dashboard: `http://localhost:3000`
- API Backend: `http://localhost:8000`
- MongoDB: `localhost:27017`

---

## API Endpoints Reference

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/health` | Health check endpoint returning DB, Edge AI, and hardware state |
| `GET` | `/api/dashboard/summary` | Aggregated live metrics, capacity utilization, and active session count |
| `POST` | `/api/predict` | Local AI demand forecasting with 95% confidence intervals |
| `GET` | `/api/predictions` | Historical prediction logs |
| `POST` | `/api/optimize` | Constrained power allocation (water-filling or advanced scheduler) |
| `POST` | `/api/optimize/active-sessions` | Automatically optimize currently connected live stalls |
| `GET` | `/api/sessions` | List EV sessions with filtering by status |
| `POST` | `/api/sessions` | Create simulated EV session with validation |
| `PUT` | `/api/sessions/{id}` | Update session priority, deadlines, or power |
| `DELETE` | `/api/sessions/{id}` | Remove EV session |
| `POST` | `/api/datasets/upload` | Upload CSV dataset for parsing and data quality audit |
| `POST` | `/api/datasets/generate-synthetic` | Generate fresh synthetic multi-month telemetry |
| `POST` | `/api/models/train` | Trigger background retraining of Random Forest model |
| `GET` | `/api/models/metrics` | Retrieve evaluation metrics (MAE, RMSE, $R^2$, feature weights) |
| `GET` | `/api/analytics/demand` | 24-hour diurnal demand profile and peak statistics |
| `GET` | `/api/analytics/cost` | 3-way financial comparison against Time-of-Use tariffs |
| `GET` | `/api/alerts` | Active transformer overload and feasibility warnings |
| `GET` | `/api/settings` | Retrieve or update station transformer limit and tariffs |

---

## Technical Highlights & Safety Guarantees

1. **Data Leakage Prevention:** Chronological partitioning ensures models are never evaluated on past rows using future data.
2. **Deterministic Transformer Constraints:** Total allocated charging power $\sum P_i$ is strictly capped at transformer limits.
3. **Graceful Fail-Soft Degradation:** If the AI model file is removed or corrupted, the optimizer automatically switches to conservative capacity heuristics without crashing.
4. **Resilient Persistence:** Works out-of-the-box with MongoDB or offline local JSON caching if MongoDB is not present.
