import React, { useState, useEffect } from 'react';
import { 
  Zap, 
  BatteryCharging, 
  Cpu, 
  DollarSign, 
  AlertTriangle, 
  CheckCircle2, 
  Clock, 
  ArrowUpRight 
} from 'lucide-react';
import { 
  AreaChart, 
  Area, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer, 
  ReferenceLine 
} from 'recharts';
import { DashboardAPI, SessionsAPI, OptimizerAPI, AnalyticsAPI } from '../services/api';
import { MetricCard, StatusBadge } from '../components/MetricCard';

export default function DashboardPage({ setActivePage }) {
  const [summary, setSummary] = useState(null);
  const [activeSessions, setActiveSessions] = useState([]);
  const [diurnalCurve, setDiurnalCurve] = useState([]);
  const [loading, setLoading] = useState(true);
  const [optimizing, setOptimizing] = useState(false);
  const [optResult, setOptResult] = useState(null);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      const [sumData, sessData, analyticsData] = await Promise.all([
        DashboardAPI.getSummary(),
        SessionsAPI.list('active'),
        AnalyticsAPI.getDemand(7)
      ]);
      setSummary(sumData);
      setActiveSessions(sessData);
      setDiurnalCurve(analyticsData.hourly_diurnal_curve || []);
    } catch (err) {
      console.error('Failed to load dashboard:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const handleQuickOptimize = async () => {
    try {
      setOptimizing(true);
      const res = await OptimizerAPI.optimizeActive('water_filling', summary?.station_capacity_kw || 150.0);
      setOptResult(res);
      await fetchDashboardData();
    } catch (err) {
      alert(`Optimization error: ${err.message}`);
    } finally {
      setOptimizing(false);
    }
  };

  if (loading && !summary) {
    return (
      <div style={{ padding: '40px', textAlign: 'center', color: '#94a3b8' }}>
        <p>Loading Edge EV Station Dashboard...</p>
      </div>
    );
  }

  const capacity = summary?.station_capacity_kw || 150.0;
  const allocated = summary?.allocated_power_kw || 0.0;
  const headroom = summary?.remaining_capacity_kw || (capacity - allocated);
  const utilization = summary?.utilization_pct || 0.0;

  return (
    <div>
      {/* Overload / Warning Banner */}
      {summary?.capacity_warning && (
        <div className="alert-banner alert-warning">
          <AlertTriangle size={20} />
          <div>
            <strong>Capacity Warning Detected:</strong> Predicted demand or active allocation approaches station transformer limit ({capacity} kW). The Edge Optimizer is throttling flexible loads.
          </div>
        </div>
      )}

      {/* Metrics Row */}
      <div className="metrics-grid">
        <MetricCard
          title="Allocated Power"
          value={allocated.toFixed(1)}
          unit="kW"
          icon={Zap}
          color={allocated > capacity ? 'rose' : 'emerald'}
          footerText={`of ${capacity} kW Hub Limit`}
          footerBadge={`${utilization}% Load`}
        />
        <MetricCard
          title="Headroom Capacity"
          value={headroom.toFixed(1)}
          unit="kW"
          icon={CheckCircle2}
          color="cyan"
          footerText="Safe Transformer Margin"
          footerBadge="Available"
        />
        <MetricCard
          title="Active EV Sessions"
          value={summary?.active_sessions_count || 0}
          unit="EVs"
          icon={BatteryCharging}
          color="purple"
          footerText={`${summary?.total_requested_energy_kwh || 0} kWh Needed`}
          footerBadge="Live Stalls"
        />
        <MetricCard
          title="Edge AI Predicted Demand"
          value={summary?.predicted_demand_kw || 0}
          unit="kW"
          icon={Cpu}
          color="amber"
          footerText={summary?.model_status}
          footerBadge="Offline AI"
        />
        <MetricCard
          title="Estimated Cost Rate"
          value={`$${summary?.estimated_hourly_cost_usd || '0.00'}`}
          unit="/hr"
          icon={DollarSign}
          color="cyan"
          footerText={summary?.current_tariff}
          footerBadge="TOU Tariff"
        />
      </div>

      {/* Main Charts & Side Actions */}
      <div className="two-col-grid">
        {/* Real-Time Demand Chart */}
        <div className="glass-card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
            <div>
              <h3 style={{ fontSize: '16px', fontWeight: 600 }}>Station Diurnal Demand & Transformer Limit</h3>
              <p style={{ fontSize: '12px', color: '#94a3b8' }}>24-Hour expected load curve vs 150 kW capacity constraint</p>
            </div>
            <span className="badge badge-cyan">Hourly Telemetry</span>
          </div>

          <div style={{ height: '300px', width: '100%' }}>
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={diurnalCurve}>
                <defs>
                  <linearGradient id="demandGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#10b981" stopOpacity={0.4}/>
                    <stop offset="95%" stopColor="#10b981" stopOpacity={0.0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                <XAxis dataKey="hour" stroke="#64748b" fontSize={11} />
                <YAxis stroke="#64748b" fontSize={11} unit=" kW" domain={[0, 180]} />
                <Tooltip 
                  contentStyle={{ background: '#0f172a', borderColor: 'rgba(255,255,255,0.1)', borderRadius: '8px' }}
                  labelStyle={{ color: '#f8fafc', fontWeight: 600 }}
                />
                <ReferenceLine y={capacity} stroke="#ef4444" strokeDasharray="4 4" label={{ value: '150 kW Limit', fill: '#ef4444', fontSize: 11, position: 'top' }} />
                <Area 
                  type="monotone" 
                  dataKey="average_demand_kw" 
                  name="Expected Demand" 
                  stroke="#10b981" 
                  strokeWidth={2}
                  fillOpacity={1} 
                  fill="url(#demandGrad)" 
                />
                <Area 
                  type="monotone" 
                  dataKey="peak_demand_kw" 
                  name="Peak Potential" 
                  stroke="#f59e0b" 
                  strokeWidth={1}
                  strokeDasharray="2 2"
                  fill="none" 
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Quick Optimizer Action & Station Health */}
        <div className="glass-card" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <h3 style={{ fontSize: '16px', fontWeight: 600 }}>Power Allocation</h3>
              <Zap size={18} color="#10b981" />
            </div>
            <p style={{ fontSize: '13px', color: '#94a3b8', lineHeight: 1.6, marginBottom: '20px' }}>
              The constrained water-filling optimizer dynamically throttles charging power across vehicles to prevent exceeding the 150 kW transformer rating while prioritizing urgent departure deadlines.
            </p>

            <div style={{ background: 'rgba(15, 23, 42, 0.6)', padding: '16px', borderRadius: '10px', marginBottom: '20px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px', fontSize: '13px' }}>
                <span style={{ color: '#94a3b8' }}>Algorithm Mode</span>
                <span style={{ fontWeight: 600, color: '#38bdf8' }}>Weighted Water-Filling</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px', fontSize: '13px' }}>
                <span style={{ color: '#94a3b8' }}>Active Stalls</span>
                <span style={{ fontWeight: 600 }}>{activeSessions.length} / 10 EVSEs</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px' }}>
                <span style={{ color: '#94a3b8' }}>Uncontrolled Baseline</span>
                <span style={{ fontWeight: 600, color: '#f87171' }}>
                  {activeSessions.reduce((acc, s) => acc + (s.max_power_kw || 22), 0).toFixed(0)} kW
                </span>
              </div>
            </div>
          </div>

          <div>
            <button 
              onClick={handleQuickOptimize} 
              disabled={optimizing || activeSessions.length === 0}
              className="btn btn-primary"
              style={{ width: '100%' }}
            >
              <Zap size={16} />
              <span>{optimizing ? 'Optimizing Power...' : 'Run Power Optimizer Now'}</span>
            </button>
            {optResult && (
              <div style={{ marginTop: '12px', fontSize: '12px', color: '#34d399', textAlign: 'center' }}>
                Allocated {optResult.total_allocated_power_kw} kW across {optResult.active_vehicles_count} EVs successfully.
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Active Charging Sessions Table */}
      <div className="glass-card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
          <div>
            <h3 style={{ fontSize: '16px', fontWeight: 600 }}>Active EV Charging Sessions</h3>
            <p style={{ fontSize: '12px', color: '#94a3b8' }}>Live simulated EV telemetry connected to smart charging stalls</p>
          </div>
          <button onClick={() => setActivePage('sessions')} className="btn btn-secondary btn-sm">
            <span>Manage All Sessions</span>
            <ArrowUpRight size={14} />
          </button>
        </div>

        <div className="table-container">
          <table className="modern-table">
            <thead>
              <tr>
                <th>Session ID</th>
                <th>Charger Stall</th>
                <th>Departure Deadline</th>
                <th>Battery SOC</th>
                <th>Target Energy</th>
                <th>Delivered</th>
                <th>Allocated Rate</th>
                <th>Priority</th>
                <th>Feasibility</th>
              </tr>
            </thead>
            <tbody>
              {activeSessions.length === 0 ? (
                <tr>
                  <td colSpan={9} style={{ textAlign: 'center', color: '#64748b', padding: '32px' }}>
                    No active charging sessions currently connected.
                  </td>
                </tr>
              ) : (
                activeSessions.map((s) => (
                  <tr key={s.session_id}>
                    <td style={{ fontWeight: 600, fontFamily: 'monospace' }}>{s.session_id}</td>
                    <td><span className="badge badge-purple">{s.charger_id}</span></td>
                    <td style={{ color: '#94a3b8' }}>
                      <Clock size={12} style={{ display: 'inline', marginRight: '4px' }} />
                      {new Date(s.departure_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </td>
                    <td>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <div style={{ width: '60px', height: '6px', background: '#334155', borderRadius: '3px', overflow: 'hidden' }}>
                          <div style={{ width: `${s.current_soc_pct || 30}%`, height: '100%', background: '#10b981' }} />
                        </div>
                        <span style={{ fontSize: '12px' }}>{s.current_soc_pct ? `${s.current_soc_pct}%` : 'N/A'}</span>
                      </div>
                    </td>
                    <td>{s.requested_energy_kwh} kWh</td>
                    <td style={{ color: '#38bdf8' }}>{s.delivered_energy_kwh} kWh</td>
                    <td style={{ fontWeight: 700, color: '#34d399' }}>{s.allocated_power_kw} kW</td>
                    <td>
                      <span className={`badge ${s.priority >= 4 ? 'badge-rose' : (s.priority === 3 ? 'badge-cyan' : 'badge-amber')}`}>
                        P{s.priority}
                      </span>
                    </td>
                    <td>
                      <StatusBadge status={s.is_achievable ? 'feasible' : 'infeasible'} />
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
