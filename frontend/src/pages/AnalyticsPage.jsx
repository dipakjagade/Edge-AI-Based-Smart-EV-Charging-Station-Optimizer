import React, { useState, useEffect } from 'react';
import { 
  TrendingDown, 
  DollarSign, 
  Zap, 
  Percent, 
  ShieldAlert, 
  Calendar, 
  Sliders 
} from 'lucide-react';
import { 
  ComposedChart, 
  Line, 
  Area, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  Legend, 
  ResponsiveContainer 
} from 'recharts';
import { AnalyticsAPI } from '../services/api';
import { MetricCard } from '../components/MetricCard';

export default function AnalyticsPage() {
  const [energyKwh, setEnergyKwh] = useState(350.0);
  const [stationLimit, setStationLimit] = useState(150.0);
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchCostAnalytics = async () => {
    try {
      setLoading(true);
      const res = await AnalyticsAPI.getCost(parseFloat(energyKwh), parseFloat(stationLimit));
      setData(res);
    } catch (err) {
      console.error('Failed to load cost analytics:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCostAnalytics();
  }, [energyKwh, stationLimit]);

  const summary = data?.comparison_summary;
  const savings = data?.simulated_savings;

  return (
    <div>
      {/* Header Info */}
      <div style={{ marginBottom: '24px' }}>
        <p style={{ fontSize: '13px', color: '#94a3b8' }}>
          Evaluate electricity procurement expenses and peak demand penalty charges under Time-of-Use (TOU) utility rate schedules. Compare uncontrolled baseline charging against basic transformer-constrained power allocation and advanced 15-minute time-of-use scheduling.
        </p>
      </div>

      {/* Interactive Controls */}
      <div className="glass-card" style={{ marginBottom: '24px' }}>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '20px', alignItems: 'flex-end' }}>
          <div className="form-group" style={{ marginBottom: 0 }}>
            <label className="form-label">Simulated Daily Energy Delivered (kWh)</label>
            <input
              type="number"
              min="50"
              max="2000"
              step="25"
              value={energyKwh}
              onChange={(e) => setEnergyKwh(e.target.value)}
              className="form-control"
            />
          </div>

          <div className="form-group" style={{ marginBottom: 0 }}>
            <label className="form-label">Station Transformer Rating (kW)</label>
            <input
              type="number"
              min="50"
              max="500"
              step="10"
              value={stationLimit}
              onChange={(e) => setStationLimit(e.target.value)}
              className="form-control"
            />
          </div>

          <div>
            <div style={{ padding: '10px 14px', background: 'rgba(15, 23, 42, 0.6)', borderRadius: '10px', border: '1px solid var(--border-color)', fontSize: '12px' }}>
              <span style={{ color: '#94a3b8' }}>TOU Rate Schedule: </span>
              <strong>Off-Peak ($0.12) &bull; Mid ($0.20) &bull; Peak ($0.35)</strong>
            </div>
          </div>
        </div>
      </div>

      {/* Savings Metric Cards */}
      {savings && (
        <div className="metrics-grid">
          <MetricCard
            title="Simulated Cost Savings"
            value={`$${savings.dollar_savings_usd}`}
            unit=""
            icon={DollarSign}
            color="emerald"
            footerText="vs Uncontrolled Baseline"
            footerBadge={`Save ${savings.percentage_savings}%`}
          />

          <MetricCard
            title="Coincident Peak Shaved"
            value={savings.peak_shaved_kw}
            unit="kW"
            icon={TrendingDown}
            color="cyan"
            footerText={`Reduced by ${savings.peak_shaved_pct}%`}
            footerBadge="Peak Shaving"
          />

          <MetricCard
            title="Demand Charge Avoided"
            value={`$${(savings.peak_shaved_kw * 12.5).toFixed(0)}`}
            unit=""
            icon={Zap}
            color="purple"
            footerText="@ $12.50 / kW Peak Penalty"
            footerBadge="Utility Savings"
          />

          <MetricCard
            title="Transformer Protection"
            value="100%"
            unit="Safe"
            icon={ShieldAlert}
            color="amber"
            footerText="Zero Transformer Overloads"
            footerBadge="Compliant"
          />
        </div>
      )}

      {/* 3-Way Comparative Strategy Table */}
      {summary && (
        <div className="glass-card" style={{ marginBottom: '24px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
            <div>
              <h3 style={{ fontSize: '16px', fontWeight: 600 }}>Three-Way Operating Strategy Comparison</h3>
              <p style={{ fontSize: '12px', color: '#94a3b8' }}>Comprehensive financial and capacity breakdown across charging policies</p>
            </div>
            <span className="badge badge-purple">Financial Audit</span>
          </div>

          <div className="table-container">
            <table className="modern-table">
              <thead>
                <tr>
                  <th>Operating Strategy</th>
                  <th>Coincident Peak (kW)</th>
                  <th>Transformer Overload?</th>
                  <th>Energy Cost (USD)</th>
                  <th>Demand Charge (USD)</th>
                  <th>Total Daily Cost</th>
                  <th>Cost Difference</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td style={{ fontWeight: 600, color: '#f87171' }}>
                    1. Uncontrolled Charging (Immediate Max)
                  </td>
                  <td>{summary.uncontrolled_baseline.peak_demand_kw} kW</td>
                  <td><span className="badge badge-rose">OVERLOAD VIOLATION</span></td>
                  <td>${summary.uncontrolled_baseline.energy_cost_usd}</td>
                  <td>${summary.uncontrolled_baseline.demand_charge_usd}</td>
                  <td style={{ fontWeight: 700, fontSize: '15px' }}>${summary.uncontrolled_baseline.total_cost_usd}</td>
                  <td style={{ color: '#94a3b8' }}>Baseline (0%)</td>
                </tr>

                <tr>
                  <td style={{ fontWeight: 600, color: '#38bdf8' }}>
                    2. Basic Water-Filling (Transformer Throttled)
                  </td>
                  <td>{summary.basic_power_allocation.peak_demand_kw} kW</td>
                  <td><span className="badge badge-emerald">Safe (Protected)</span></td>
                  <td>${summary.basic_power_allocation.energy_cost_usd}</td>
                  <td>${summary.basic_power_allocation.demand_charge_usd}</td>
                  <td style={{ fontWeight: 700, fontSize: '15px' }}>${summary.basic_power_allocation.total_cost_usd}</td>
                  <td style={{ color: '#34d399', fontWeight: 600 }}>
                    -${(summary.uncontrolled_baseline.total_cost_usd - summary.basic_power_allocation.total_cost_usd).toFixed(2)}
                  </td>
                </tr>

                <tr>
                  <td style={{ fontWeight: 600, color: '#34d399' }}>
                    3. Advanced 15-min Time-of-Use Scheduling
                  </td>
                  <td>{summary.advanced_tou_scheduling.peak_demand_kw} kW</td>
                  <td><span className="badge badge-emerald">Safe (Optimal)</span></td>
                  <td>${summary.advanced_tou_scheduling.energy_cost_usd}</td>
                  <td>${summary.advanced_tou_scheduling.demand_charge_usd}</td>
                  <td style={{ fontWeight: 700, fontSize: '15px', color: '#10b981' }}>${summary.advanced_tou_scheduling.total_cost_usd}</td>
                  <td style={{ color: '#10b981', fontWeight: 700 }}>
                    -${savings?.dollar_savings_usd} ({savings?.percentage_savings}%)
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* 24-Hour Diurnal Load and Cost Curve */}
      {data?.hourly_load_and_cost_curve && (
        <div className="glass-card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
            <div>
              <h3 style={{ fontSize: '16px', fontWeight: 600 }}>24-Hour Load Profile & Time-of-Use Tariff Overlay</h3>
              <p style={{ fontSize: '12px', color: '#94a3b8' }}>Visualizing how smart scheduling shifts energy draw into cheap off-peak hours</p>
            </div>
            <span className="badge badge-emerald">Load Shifting</span>
          </div>

          <div style={{ height: '340px', width: '100%' }}>
            <ResponsiveContainer width="100%" height="100%">
              <ComposedChart data={data.hourly_load_and_cost_curve}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                <XAxis dataKey="hour" stroke="#64748b" fontSize={11} />
                <YAxis yAxisId="left" stroke="#64748b" fontSize={11} unit=" kW" domain={[0, 180]} />
                <YAxis yAxisId="right" orientation="right" stroke="#f59e0b" fontSize={11} unit=" $" domain={[0, 0.45]} />
                <Tooltip 
                  contentStyle={{ background: '#0f172a', borderColor: 'rgba(255,255,255,0.1)', borderRadius: '8px' }}
                  labelStyle={{ color: '#f8fafc', fontWeight: 600 }}
                />
                <Legend wrapperStyle={{ paddingTop: '10px' }} />
                <Area yAxisId="left" type="monotone" dataKey="uncontrolled_load_kw" name="Uncontrolled Load" fill="#f87171" stroke="#f87171" fillOpacity={0.15} />
                <Area yAxisId="left" type="monotone" dataKey="optimized_load_kw" name="Optimized Load" fill="#10b981" stroke="#10b981" fillOpacity={0.25} />
                <Line yAxisId="right" type="stepAfter" dataKey="tariff_rate_usd" name="Tariff Rate ($/kWh)" stroke="#f59e0b" strokeWidth={2} dot={false} />
              </ComposedChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}
    </div>
  );
}
