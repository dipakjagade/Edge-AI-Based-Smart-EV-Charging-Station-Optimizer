import React from 'react';
import { 
  BookOpen, 
  ExternalLink, 
  Cpu, 
  Zap, 
  Server, 
  ShieldCheck, 
  Terminal, 
  Code2 
} from 'lucide-react';

export default function DocumentationPage() {
  return (
    <div>
      {/* Header Info */}
      <div style={{ marginBottom: '24px' }}>
        <p style={{ fontSize: '13px', color: '#94a3b8' }}>
          Comprehensive architecture, mathematical algorithms, edge deployment guide, and API specification for the Edge AI Based Smart EV Charging Station Optimizer.
        </p>
      </div>

      {/* Quick Links Card */}
      <div className="glass-card" style={{ marginBottom: '24px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px' }}>
          <div>
            <h3 style={{ fontSize: '16px', fontWeight: 600 }}>Interactive API Documentation</h3>
            <p style={{ fontSize: '12px', color: '#94a3b8' }}>FastAPI Swagger UI and OpenAPI JSON endpoints</p>
          </div>

          <div style={{ display: 'flex', gap: '12px' }}>
            <a 
              href="http://localhost:8000/docs" 
              target="_blank" 
              rel="noreferrer"
              className="btn btn-primary btn-sm"
            >
              <span>Open Swagger UI</span>
              <ExternalLink size={14} />
            </a>
            <a 
              href="http://localhost:8000/health" 
              target="_blank" 
              rel="noreferrer"
              className="btn btn-secondary btn-sm"
            >
              <span>Live Health Status</span>
              <ExternalLink size={14} />
            </a>
          </div>
        </div>
      </div>

      {/* Architecture Overview */}
      <div className="glass-card" style={{ marginBottom: '24px' }}>
        <h3 style={{ fontSize: '16px', fontWeight: 600, marginBottom: '12px' }}>System Architecture</h3>
        <p style={{ fontSize: '13px', color: '#94a3b8', lineHeight: 1.6, marginBottom: '20px' }}>
          The system follows an edge-first, cloud-independent architecture designed for high reliability, zero latency, and safe fail-soft operation on local mini-PCs or industrial edge computers.
        </p>

        <div style={{ background: '#0a0f1d', padding: '20px', borderRadius: '12px', border: '1px solid var(--border-color)', fontFamily: 'monospace', fontSize: '12px', lineHeight: 1.6, overflowX: 'auto', color: '#38bdf8' }}>
          <pre>{`+---------------------------------------------------------------------------------+
|                                 EDGE HARDWARE                                   |
|                     (Raspberry Pi 5 / Mini PC / Edge Server)                    |
|                                                                                 |
|  +---------------------------------------------------------------------------+  |
|  |                            React Dashboard (Vite)                         |  |
|  |  [Dashboard] [Sessions] [Predict] [Optimizer] [Datasets] [Model Train]    |  |
|  |  [Cost & Energy Analytics] [Alerts & Health] [Settings] [Documentation]   |  |
|  +-------------------------------------+-------------------------------------+  |
|                                        | HTTP/REST (Axios)                      |
|                                        v                                        |
|  +---------------------------------------------------------------------------+  |
|  |                            FastAPI Backend                                |  |
|  |  - Auth & Security (JWT, CORS, Strict Validation)                         |  |
|  |  - REST Endpoints (/health, /sessions, /predict, /optimize, /analytics)   |  |
|  +---------------------+-------------------+------------------+---------------+  |
|                        |                   |                  |                 |
|                        v                   v                  v                 |
|         +-----------------------+ +------------------+ +--------------------+   |
|         | Demand Prediction     | | Power Optimizer  | | Dataset & Tariff   |   |
|         | - Scikit-learn RF     | | - Weighted Water-| | - CSV Parsing      |   |
|         | - Feature Validation  | |   Filling        | | - Column Mapping   |   |
|         | - Safe Fallback Mode  | | - 15-min Advanced| | - Quality Summary  |   |
|         | - MAE & RMSE metrics  | |   Time Scheduler | | - TOU Tariffs      |   |
|         +-----------+-----------+ +--------+---------+ +---------+----------+   |
|                     |                      |                     |              |
|                     +----------------------+---------------------+              |
|                                            |                                    |
|                                            v                                    |
|         +---------------------------------------------------------------+       |
|         |                      Persistence Layer                        |       |
|         |  - MongoDB (PyMongo / Motor)                                  |       |
|         |  - Resilient In-Memory / Local Cache Fallback                 |       |
|         +---------------------------------------------------------------+       |
+---------------------------------------------------------------------------------+`}</pre>
        </div>
      </div>

      {/* Algorithms Explanation */}
      <div className="equal-col-grid" style={{ marginBottom: '24px' }}>
        <div className="glass-card">
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '14px' }}>
            <Zap size={20} color="#10b981" />
            <h3 style={{ fontSize: '16px', fontWeight: 600 }}>1. Weighted Water-Filling Allocation</h3>
          </div>
          <p style={{ fontSize: '13px', color: '#94a3b8', lineHeight: 1.6, marginBottom: '14px' }}>
            Solves instantaneous capacity distribution under transformer constraints:
          </p>
          <ul style={{ fontSize: '12px', color: '#cbd5e1', lineHeight: 1.8, paddingLeft: '18px' }}>
            <li><strong>Transformer Constraint:</strong> &sum; P<sub>i</sub> &le; P<sub>station_max</sub> (150 kW)</li>
            <li><strong>Charger Limit:</strong> 0 &le; P<sub>i</sub> &le; P<sub>max, i</sub></li>
            <li><strong>Urgency Metric:</strong> U<sub>i</sub> = E<sub>rem, i</sub> / &Delta;t<sub>rem, i</sub> (kW needed to finish on deadline)</li>
            <li><strong>Priority Weight:</strong> W<sub>i</sub> = Priority<sub>i</sub> &times; max(0.5, U<sub>i</sub>)</li>
            <li><strong>Redistribution:</strong> Iteratively saturates vehicles at individual limits and redistributes excess transformer power to hungry vehicles.</li>
          </ul>
        </div>

        <div className="glass-card">
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '14px' }}>
            <Cpu size={20} color="#38bdf8" />
            <h3 style={{ fontSize: '16px', fontWeight: 600 }}>2. Advanced Multi-Period Scheduling</h3>
          </div>
          <p style={{ fontSize: '13px', color: '#94a3b8', lineHeight: 1.6, marginBottom: '14px' }}>
            Schedules charging energy across 15-minute time slots to minimize electricity procurement costs:
          </p>
          <ul style={{ fontSize: '12px', color: '#cbd5e1', lineHeight: 1.8, paddingLeft: '18px' }}>
            <li><strong>Cost Minimization:</strong> min &sum;<sub>k</sub> c<sub>k</sub> &times; (&sum;<sub>i</sub> P<sub>i, k</sub> &times; 0.25h)</li>
            <li><strong>Time-of-Use Alignment:</strong> Fills valley hours ($0.12/kWh) before on-peak ($0.35/kWh)</li>
            <li><strong>Deadline Feasibility:</strong> Ensures &sum;<sub>k</sub> P<sub>i, k</sub> &times; 0.25 &ge; E<sub>requested, i</sub></li>
            <li><strong>Peak Shaving:</strong> Prevents coincident spike over transformer capacity.</li>
          </ul>
        </div>
      </div>

      {/* Edge Deployment Guide */}
      <div className="glass-card">
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '16px' }}>
          <Terminal size={20} color="#c084fc" />
          <h3 style={{ fontSize: '16px', fontWeight: 600 }}>Edge Deployment Guide (Raspberry Pi 5 / Mini PC)</h3>
        </div>

        <p style={{ fontSize: '13px', color: '#94a3b8', lineHeight: 1.6, marginBottom: '16px' }}>
          To deploy this optimizer on a Raspberry Pi 5 (8GB) or edge mini-PC running Debian/Ubuntu:
        </p>

        <div style={{ background: '#0a0f1d', padding: '16px', borderRadius: '10px', border: '1px solid var(--border-color)', fontFamily: 'monospace', fontSize: '12px', color: '#34d399', lineHeight: 1.6, overflowX: 'auto' }}>
          <pre>{`# 1. Clone repository to edge device
git clone https://github.com/project/edge-ai-ev-optimizer.git /opt/edge-ev-hub
cd /opt/edge-ev-hub

# 2. Setup Python environment
python3 -m venv venv
source venv/bin/activate
pip install -r backend/requirements.txt

# 3. Train or load pre-trained edge model
python backend/ml/generate_synthetic_data.py --days 90
python backend/ml/train_model.py

# 4. Run backend service with systemd (starts on boot)
sudo cp deployment/edge-ev-optimizer.service /etc/systemd/system/
sudo systemctl enable --now edge-ev-optimizer

# 5. Serve frontend dashboard locally
cd frontend && npm install && npm run build
sudo apt install nginx -y
sudo cp deployment/nginx.conf /etc/nginx/sites-available/default
sudo systemctl restart nginx`}</pre>
        </div>
      </div>
    </div>
  );
}
