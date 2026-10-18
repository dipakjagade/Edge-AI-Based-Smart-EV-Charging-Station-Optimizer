import React, { useState, useEffect } from 'react';
import { 
  Zap, 
  Clock, 
  AlertTriangle, 
  CheckCircle2, 
  BarChart3, 
  Layers, 
  Sliders, 
  DollarSign 
} from 'lucide-react';
import { 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  Legend, 
  ResponsiveContainer, 
  ReferenceLine 
} from 'recharts';
import { OptimizerAPI, SessionsAPI } from '../services/api';
import { MetricCard, StatusBadge } from '../components/MetricCard';

export default function OptimizerPage() {
  const [mode, setMode] = useState('water_filling');
  const [stationLimit, setStationLimit] = useState(150.0);
  const [activeSessions, setActiveSessions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [optResult, setOptResult] = useState(null);

  const fetchActiveSessions = async () => {
    try {
      const data = await SessionsAPI.list('active');
      setActiveSessions(data);
    } catch (err) {
      console.error('Failed to fetch active sessions:', err);
    }
  };

  useEffect(() => {
    fetchActiveSessions();
  }, []);

  const handleRunOptimizer = async () => {
    try {
      setLoading(true);
      const res = await OptimizerAPI.optimizeActive(mode, parseFloat(stationLimit));
      setOptResult(res);
      fetchActiveSessions();
    } catch (err) {
      alert(`Optimization failed: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      {/* Header Info */}
      <div style={{ marginBottom: '24px' }}>
        <p style={{ fontSize: '13px', color: '#94a3b8' }}>
          Distribute available electrical capacity across active EV stalls using mathematical power allocation algorithms. Ensures the station's 150 kW transformer rating is never exceeded while honoring departure deadlines.
        </p>
      </div>

      {/* Control Panel */}
      <div className="glass-card" style={{ marginBottom: '24px' }}>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '20px', alignItems: 'flex-end' }}>
          <div className="form-group" style={{ marginBottom: 0 }}>
            <label className="form-label">Optimization Algorithm Mode</label>
            <select
              value={mode}
              onChange={(e) => setMode(e.target.value)}
              className="form-control"
            >
              <option value="water_filling">Weighted Water-Filling (Instantaneous)</option>
              <option value="advanced_scheduler">Advanced 15-Minute Time-Slot Scheduler</option>
            </select>
          </div>

          <div className="form-group" style={{ marginBottom: 0 }}>
            <label className="form-label">Station Transformer Limit (kW)</label>
            <input
              type="number"
              min="50"
              max="1000"
              step="10"
              value={stationLimit}
              onChange={(e) => setStationLimit(e.target.value)}
              className="form-control"
            />
          </div>

          <div className="form-group" style={{ marginBottom: 0 }}>
            <label className="form-label">Connected EV Stalls</label>
            <div style={{ padding: '10px 14px', background: 'rgba(15, 23, 42, 0.6)', borderRadius: '10px', border: '1px solid var(--border-color)', fontSize: '14px', fontWeight: 600 }}>
              {activeSessions.length} Active Vehicles
            </div>
          </div>

          <div>
            <button
              onClick={handleRunOptimizer}
              disabled={loading || activeSessions.length === 0}
              className="btn btn-primary"
              style={{ width: '100%', height: '42px' }}
            >
              <Zap size={16} />
              <span>{loading ? 'Solving Constraints...' : 'Run Power Optimizer'}</span>
            </button>
          </div>
        </div>
      </div>

      {/* Optimization Results */}
      {optResult && (
        <>
          {/* Summary Cards */}
          <div className="metrics-grid">
            <MetricCard
              title="Allocated Total Power"
              value={optResult.total_allocated_power_kw}
              unit="kW"
              icon={Zap}
              color={optResult.total_allocated_power_kw > optResult.station_power_limit_kw ? 'rose' : 'emerald'}
              footerText={`Limit: ${optResult.station_power_limit_kw} kW`}
              footerBadge={`${Math.round((optResult.total_allocated_power_kw / optResult.station_power_limit_kw) * 100)}% Utilized`}
            />

            <MetricCard
              title="Headroom Unused"
              value={optResult.unused_capacity_kw}
              unit="kW"
              icon={CheckCircle2}
              color="cyan"
              footerText="Reserve Capacity"
              footerBadge="Protected"
            />

            <MetricCard
              title="Feasibility Status"
              value={optResult.infeasible_sessions_count === 0 ? '100%' : `${optResult.active_vehicles_count - optResult.infeasible_sessions_count}/${optResult.active_vehicles_count}`}
              unit={optResult.infeasible_sessions_count === 0 ? 'Feasible' : 'Satisfied'}
              icon={optResult.infeasible_sessions_count === 0 ? CheckCircle2 : AlertTriangle}
              color={optResult.infeasible_sessions_count === 0 ? 'emerald' : 'amber'}
              footerText={optResult.infeasible_sessions_count === 0 ? 'All Deadlines Achievable' : `${optResult.infeasible_sessions_count} EVs Throttled/Bottlenecked`}
              footerBadge={optResult.infeasible_sessions_count === 0 ? 'Optimal' : 'Bottleneck'}
            />

            <MetricCard
              title="Peak Shaving Reduction"
              value={optResult.cost_summary.demand_reduction_kw || optResult.cost_summary.simulated_cost_savings_usd || '0.0'}
              unit={mode === 'water_filling' ? 'kW' : 'USD'}
              icon={BarChart3}
              color="purple"
              footerText={mode === 'water_filling' ? `${optResult.cost_summary.peak_shaving_pct}% Peak Shaved` : `${optResult.cost_summary.savings_percentage}% TOU Savings`}
              footerBadge="Cost Optimized"
            />
          </div>

          {/* Time Slot Schedule Chart (if Advanced Scheduler) */}
          {optResult.time_slot_schedule && (
            <div className="glass-card" style={{ marginBottom: '24px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
                <div>
                  <h3 style={{ fontSize: '16px', fontWeight: 600 }}>15-Minute Discretized Time-Slot Schedule</h3>
                  <p style={{ fontSize: '12px', color: '#94a3b8' }}>Load distribution per interval aligned with Time-of-Use electricity tariffs</p>
                </div>
                <span className="badge badge-cyan">Multi-Period Horizon</span>
              </div>

              <div style={{ height: '320px', width: '100%' }}>
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={optResult.time_slot_schedule}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                    <XAxis dataKey="slot_time" stroke="#64748b" fontSize={11} />
                    <YAxis stroke="#64748b" fontSize={11} unit=" kW" domain={[0, stationLimit * 1.1]} />
                    <Tooltip 
                      contentStyle={{ background: '#0f172a', borderColor: 'rgba(255,255,255,0.1)', borderRadius: '8px' }}
                      labelStyle={{ color: '#f8fafc', fontWeight: 600 }}
                    />
                    <ReferenceLine y={stationLimit} stroke="#ef4444" strokeDasharray="4 4" label={{ value: '150 kW Limit', fill: '#ef4444', fontSize: 11 }} />
                    <Bar dataKey="total_allocated_kw" name="Scheduled Power" fill="#10b981" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          )}

          {/* Allocation Breakdown Table */}
          <div className="glass-card">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <div>
                <h3 style={{ fontSize: '16px', fontWeight: 600 }}>Vehicle Power Allocations & Deadline Feasibility</h3>
                <p style={{ fontSize: '12px', color: '#94a3b8' }}>Optimized charging rates adhering to charger hardware and station capacity</p>
              </div>
              <span className="badge badge-purple">{optResult.allocations.length} Allocations</span>
            </div>

            <div className="table-container">
              <table className="modern-table">
                <thead>
                  <tr>
                    <th>Session ID</th>
                    <th>Charger ID</th>
                    <th>Allocated Power</th>
                    <th>Charger Limit</th>
                    <th>Remaining Energy</th>
                    <th>Est. Completion</th>
                    <th>Departure Deadline</th>
                    <th>Deadline Feasible?</th>
                    <th>Bottleneck Diagnosis</th>
                  </tr>
                </thead>
                <tbody>
                  {optResult.allocations.map((a) => (
                    <tr key={a.session_id}>
                      <td style={{ fontWeight: 600, fontFamily: 'monospace' }}>{a.session_id}</td>
                      <td><span className="badge badge-purple">{a.charger_id}</span></td>
                      <td style={{ fontWeight: 700, color: '#34d399', fontSize: '14px' }}>
                        {a.allocated_power_kw} kW
                      </td>
                      <td style={{ color: '#94a3b8' }}>{a.max_power_kw} kW</td>
                      <td>{a.remaining_energy_kwh} kWh</td>
                      <td style={{ color: '#38bdf8' }}>
                        <Clock size={12} style={{ display: 'inline', marginRight: '4px' }} />
                        {a.estimated_completion_time ? new Date(a.estimated_completion_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : 'Indefinite'}
                      </td>
                      <td style={{ color: '#94a3b8' }}>
                        {new Date(a.departure_deadline).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </td>
                      <td>
                        <StatusBadge status={a.can_complete_before_departure ? 'feasible' : 'infeasible'} />
                      </td>
                      <td style={{ maxWidth: '280px', fontSize: '11px', color: a.can_complete_before_departure ? '#64748b' : '#fbbf24' }}>
                        {a.infeasibility_reason || 'Nominal: on schedule to satisfy requested energy before deadline.'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
