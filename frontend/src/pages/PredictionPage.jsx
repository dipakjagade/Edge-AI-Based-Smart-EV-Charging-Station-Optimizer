import React, { useState, useEffect } from 'react';
import { 
  Cpu, 
  Zap, 
  TrendingUp, 
  AlertTriangle, 
  ShieldCheck, 
  Clock, 
  HelpCircle, 
  History 
} from 'lucide-react';
import { PredictionAPI } from '../services/api';
import { MetricCard } from '../components/MetricCard';

export default function PredictionPage() {
  const [form, setForm] = useState({
    hour: new Date().getHours(),
    day_of_week: new Date().getDay() === 0 ? 6 : new Date().getDay() - 1,
    active_sessions: 6,
    total_requested_energy_kwh: 180.0,
    avg_battery_soc: 35.0,
    tariff_rate: 0.20,
    station_capacity_kw: 150.0
  });

  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [history, setHistory] = useState([]);

  const fetchHistory = async () => {
    try {
      const data = await PredictionAPI.getHistory(15);
      setHistory(data);
    } catch (err) {
      console.error('Failed to fetch prediction history:', err);
    }
  };

  useEffect(() => {
    fetchHistory();
  }, []);

  const handlePredict = async (e) => {
    e.preventDefault();
    try {
      setLoading(true);
      const res = await PredictionAPI.predict({
        ...form,
        hour: parseInt(form.hour),
        day_of_week: parseInt(form.day_of_week),
        active_sessions: parseInt(form.active_sessions),
        total_requested_energy_kwh: parseFloat(form.total_requested_energy_kwh),
        avg_battery_soc: parseFloat(form.avg_battery_soc),
        tariff_rate: parseFloat(form.tariff_rate),
        station_capacity_kw: parseFloat(form.station_capacity_kw)
      });
      setResult(res);
      fetchHistory();
    } catch (err) {
      alert(`Prediction failed: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const daysOfWeek = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];

  return (
    <div>
      {/* Header Info */}
      <div style={{ marginBottom: '24px' }}>
        <p style={{ fontSize: '13px', color: '#94a3b8' }}>
          Edge AI inference executes a local Scikit-learn Random Forest model trained on chronological EV hub telemetry. It forecasts multi-session aggregate electrical power draw without external cloud dependencies.
        </p>
      </div>

      <div className="two-col-grid">
        {/* Prediction Form */}
        <div className="glass-card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
            <h3 style={{ fontSize: '16px', fontWeight: 600 }}>Forecast Simulation Parameters</h3>
            <span className="badge badge-emerald">Edge Offline Mode</span>
          </div>

          <form onSubmit={handlePredict}>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
              <div className="form-group">
                <label className="form-label">Hour of Day (0 - 23)</label>
                <input
                  type="number"
                  min="0"
                  max="23"
                  value={form.hour}
                  onChange={(e) => setForm({ ...form, hour: e.target.value })}
                  className="form-control"
                />
              </div>

              <div className="form-group">
                <label className="form-label">Day of Week</label>
                <select
                  value={form.day_of_week}
                  onChange={(e) => setForm({ ...form, day_of_week: e.target.value })}
                  className="form-control"
                >
                  {daysOfWeek.map((d, i) => (
                    <option key={i} value={i}>{d}</option>
                  ))}
                </select>
              </div>
            </div>

            <div className="form-group">
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
                <label className="form-label">Concurrent Active EVs: {form.active_sessions}</label>
                <span style={{ fontSize: '12px', color: '#6ee7b7' }}>Max 10 Stalls</span>
              </div>
              <input
                type="range"
                min="0"
                max="10"
                value={form.active_sessions}
                onChange={(e) => setForm({ 
                  ...form, 
                  active_sessions: e.target.value,
                  total_requested_energy_kwh: (e.target.value * 30.0).toFixed(0)
                })}
                style={{ width: '100%', accentColor: '#10b981' }}
              />
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
              <div className="form-group">
                <label className="form-label">Total Requested Energy (kWh)</label>
                <input
                  type="number"
                  min="0"
                  max="500"
                  step="5"
                  value={form.total_requested_energy_kwh}
                  onChange={(e) => setForm({ ...form, total_requested_energy_kwh: e.target.value })}
                  className="form-control"
                />
              </div>

              <div className="form-group">
                <label className="form-label">Average Incoming SOC (%)</label>
                <input
                  type="number"
                  min="5"
                  max="95"
                  value={form.avg_battery_soc}
                  onChange={(e) => setForm({ ...form, avg_battery_soc: e.target.value })}
                  className="form-control"
                />
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
              <div className="form-group">
                <label className="form-label">Tariff Rate ($/kWh)</label>
                <input
                  type="number"
                  min="0.05"
                  max="1.0"
                  step="0.01"
                  value={form.tariff_rate}
                  onChange={(e) => setForm({ ...form, tariff_rate: e.target.value })}
                  className="form-control"
                />
              </div>

              <div className="form-group">
                <label className="form-label">Station Transformer Limit (kW)</label>
                <input
                  type="number"
                  min="50"
                  max="500"
                  value={form.station_capacity_kw}
                  onChange={(e) => setForm({ ...form, station_capacity_kw: e.target.value })}
                  className="form-control"
                />
              </div>
            </div>

            <button type="submit" disabled={loading} className="btn btn-primary" style={{ width: '100%', marginTop: '10px' }}>
              <Cpu size={16} />
              <span>{loading ? 'Evaluating Model On Edge...' : 'Execute Demand Prediction'}</span>
            </button>
          </form>
        </div>

        {/* Prediction Output & Confidence Card */}
        <div>
          {result ? (
            <div className="glass-card" style={{ height: '100%', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                  <h3 style={{ fontSize: '16px', fontWeight: 600 }}>Edge Inference Output</h3>
                  <span className={`badge ${result.fallback_used ? 'badge-amber' : 'badge-emerald'}`}>
                    {result.model_type}
                  </span>
                </div>

                {result.capacity_exceeded && (
                  <div className="alert-banner alert-danger" style={{ marginBottom: '16px' }}>
                    <AlertTriangle size={18} />
                    <span><strong>Transformer Capacity Violation!</strong> Forecasted demand ({result.predicted_demand_kw} kW) exceeds the {form.station_capacity_kw} kW limit. Throttling required.</span>
                  </div>
                )}

                <div style={{ textAlign: 'center', padding: '24px 0', borderBottom: '1px solid rgba(255,255,255,0.08)' }}>
                  <span style={{ fontSize: '13px', color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                    Forecasted Station Demand
                  </span>
                  <div style={{ fontSize: '48px', fontWeight: 800, fontFamily: 'monospace', color: '#10b981', margin: '8px 0' }}>
                    {result.predicted_demand_kw} <span style={{ fontSize: '20px', color: '#94a3b8' }}>kW</span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'center', gap: '8px', fontSize: '12px', color: '#64748b' }}>
                    <span>95% Confidence Band:</span>
                    <strong style={{ color: '#38bdf8' }}>
                      [{result.confidence_interval.lower_kw} kW &mdash; {result.confidence_interval.upper_kw} kW]
                    </strong>
                  </div>
                </div>

                <div style={{ padding: '20px 0', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', fontSize: '13px' }}>
                  <div style={{ background: 'rgba(15, 23, 42, 0.5)', padding: '12px', borderRadius: '8px' }}>
                    <span style={{ color: '#94a3b8' }}>Naive Persistence Baseline</span>
                    <div style={{ fontWeight: 700, fontSize: '16px', marginTop: '4px' }}>
                      {result.baseline_prediction_kw} kW
                    </div>
                  </div>

                  <div style={{ background: 'rgba(15, 23, 42, 0.5)', padding: '12px', borderRadius: '8px' }}>
                    <span style={{ color: '#94a3b8' }}>Transformer Headroom</span>
                    <div style={{ fontWeight: 700, fontSize: '16px', marginTop: '4px', color: result.capacity_headroom_kw < 0 ? '#f87171' : '#34d399' }}>
                      {result.capacity_headroom_kw} kW
                    </div>
                  </div>
                </div>
              </div>

              <div style={{ fontSize: '11px', color: '#64748b', borderTop: '1px solid rgba(255,255,255,0.06)', paddingTop: '12px' }}>
                Prediction ID: {result.id} &bull; Version: {result.model_version} &bull; Timestamp: {new Date(result.timestamp).toLocaleTimeString()}
              </div>
            </div>
          ) : (
            <div className="glass-card" style={{ height: '100%', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', textAlign: 'center', color: '#64748b', padding: '40px' }}>
              <Cpu size={48} style={{ opacity: 0.3, marginBottom: '16px' }} />
              <h4 style={{ color: '#94a3b8', fontSize: '15px', marginBottom: '8px' }}>No Active Prediction Yet</h4>
              <p style={{ fontSize: '13px', maxWidth: '320px' }}>
                Adjust simulation parameters on the left and click "Execute Demand Prediction" to run offline inference.
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Historical Inferences Table */}
      <div className="glass-card" style={{ marginTop: '24px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
          <h3 style={{ fontSize: '16px', fontWeight: 600 }}>Recent Edge Predictions Log</h3>
          <span className="badge badge-purple">{history.length} Inferences</span>
        </div>

        <div className="table-container">
          <table className="modern-table">
            <thead>
              <tr>
                <th>Prediction ID</th>
                <th>Timestamp</th>
                <th>Active EVs</th>
                <th>Predicted Demand</th>
                <th>95% Interval</th>
                <th>Transformer Headroom</th>
                <th>Model Type</th>
              </tr>
            </thead>
            <tbody>
              {history.length === 0 ? (
                <tr>
                  <td colSpan={7} style={{ textAlign: 'center', color: '#64748b', padding: '24px' }}>
                    No predictions recorded yet.
                  </td>
                </tr>
              ) : (
                history.map((h) => (
                  <tr key={h.id}>
                    <td style={{ fontFamily: 'monospace', fontWeight: 600 }}>{h.id}</td>
                    <td style={{ color: '#94a3b8' }}>{new Date(h.timestamp).toLocaleTimeString()}</td>
                    <td>{h.input_features.active_sessions} EVs</td>
                    <td style={{ fontWeight: 700, color: '#34d399' }}>{h.predicted_demand_kw} kW</td>
                    <td style={{ color: '#94a3b8' }}>
                      [{h.confidence_interval.lower_kw} &ndash; {h.confidence_interval.upper_kw}]
                    </td>
                    <td style={{ color: h.capacity_headroom_kw < 0 ? '#f87171' : '#34d399', fontWeight: 600 }}>
                      {h.capacity_headroom_kw} kW
                    </td>
                    <td>
                      <span className={`badge ${h.fallback_used ? 'badge-amber' : 'badge-emerald'}`}>
                        {h.model_type}
                      </span>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
