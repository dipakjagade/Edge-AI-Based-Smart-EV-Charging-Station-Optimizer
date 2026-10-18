import React, { useState, useEffect } from 'react';
import { 
  BellRing, 
  CheckCircle, 
  AlertTriangle, 
  Info, 
  ShieldCheck, 
  HardDrive, 
  Cpu, 
  Database, 
  Check 
} from 'lucide-react';
import { AlertsAPI, DashboardAPI } from '../services/api';
import { MetricCard, StatusBadge } from '../components/MetricCard';

export default function AlertsHealthPage() {
  const [alerts, setAlerts] = useState([]);
  const [health, setHealth] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchData = async () => {
    try {
      setLoading(true);
      const [alertsData, healthData] = await Promise.all([
        AlertsAPI.list(),
        DashboardAPI.getHealth()
      ]);
      setAlerts(alertsData);
      setHealth(healthData);
    } catch (err) {
      console.error('Failed to load alerts & health:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleResolve = async (id) => {
    try {
      await AlertsAPI.resolve(id);
      fetchData();
    } catch (err) {
      alert(`Failed to resolve alert: ${err.message}`);
    }
  };

  return (
    <div>
      {/* Header Info */}
      <div style={{ marginBottom: '24px' }}>
        <p style={{ fontSize: '13px', color: '#94a3b8' }}>
          Continuously monitors edge hardware health, transformer load constraints, AI prediction engine availability, database persistence layers, and deadline feasibility.
        </p>
      </div>

      {/* Edge System Health Cards */}
      <div className="metrics-grid">
        <MetricCard
          title="Edge Hardware Status"
          value={health?.status === 'healthy' ? 'Operational' : 'Attention'}
          unit=""
          icon={Cpu}
          color={health?.status === 'healthy' ? 'emerald' : 'amber'}
          footerText="Offline Edge Computer"
          footerBadge="No Cloud Needed"
        />

        <MetricCard
          title="Demand AI Model"
          value={health?.model_loaded ? 'Online' : 'Fallback'}
          unit=""
          icon={ShieldCheck}
          color={health?.model_loaded ? 'emerald' : 'amber'}
          footerText="Random Forest Regressor"
          footerBadge="Local Joblib"
        />

        <MetricCard
          title="Database Persistence"
          value={health?.database?.status === 'connected' ? 'MongoDB Live' : 'Local JSON Cache'}
          unit=""
          icon={Database}
          color={health?.database?.status === 'connected' ? 'emerald' : 'cyan'}
          footerText={health?.database?.database || 'Local Store'}
          footerBadge="Zero Data Loss"
        />

        <MetricCard
          title="Active System Alerts"
          value={alerts.length}
          unit="Active"
          icon={BellRing}
          color={alerts.length === 0 ? 'emerald' : 'amber'}
          footerText="Real-time Health Engine"
          footerBadge={alerts.length === 0 ? 'Normal' : 'Attention'}
        />
      </div>

      {/* Alerts Feed */}
      <div className="glass-card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
          <div>
            <h3 style={{ fontSize: '16px', fontWeight: 600 }}>Active System Alerts & Diagnostics Feed</h3>
            <p style={{ fontSize: '12px', color: '#94a3b8' }}>Automatic state-based notifications for capacity overloads, bottlenecks, and hardware fallbacks</p>
          </div>
          <span className="badge badge-purple">{alerts.length} Warnings/Notices</span>
        </div>

        {alerts.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '48px 20px', color: '#64748b' }}>
            <CheckCircle size={44} style={{ color: '#10b981', marginBottom: '12px' }} />
            <h4 style={{ color: '#f8fafc', fontSize: '16px', marginBottom: '4px' }}>All Systems Nominal</h4>
            <p style={{ fontSize: '13px' }}>No transformer capacity violations or hardware issues detected.</p>
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {alerts.map((alt) => {
              const isWarning = alt.severity === 'warning';
              const isCritical = alt.severity === 'critical';
              const borderCol = isCritical ? 'rgba(239, 68, 68, 0.4)' : (isWarning ? 'rgba(245, 158, 11, 0.4)' : 'rgba(6, 182, 212, 0.4)');
              const bgCol = isCritical ? 'rgba(239, 68, 68, 0.08)' : (isWarning ? 'rgba(245, 158, 11, 0.08)' : 'rgba(6, 182, 212, 0.08)');

              return (
                <div
                  key={alt.id}
                  style={{
                    padding: '16px 20px',
                    borderRadius: '12px',
                    border: `1px solid ${borderCol}`,
                    background: bgCol,
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'flex-start',
                    gap: '16px'
                  }}
                >
                  <div style={{ display: 'flex', gap: '14px', alignItems: 'flex-start' }}>
                    <div style={{ marginTop: '2px' }}>
                      {isCritical ? (
                        <AlertTriangle size={20} color="#f87171" />
                      ) : isWarning ? (
                        <AlertTriangle size={20} color="#fbbf24" />
                      ) : (
                        <Info size={20} color="#38bdf8" />
                      )}
                    </div>
                    <div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '4px' }}>
                        <span style={{ fontWeight: 600, fontSize: '14px', color: '#f8fafc' }}>{alt.title}</span>
                        <span className={`badge ${isCritical ? 'badge-rose' : (isWarning ? 'badge-amber' : 'badge-cyan')}`} style={{ textTransform: 'uppercase', fontSize: '10px' }}>
                          {alt.severity}
                        </span>
                        <span style={{ fontSize: '11px', color: '#64748b' }}>Source: {alt.source}</span>
                      </div>
                      <p style={{ fontSize: '13px', color: '#cbd5e1', lineHeight: 1.5 }}>
                        {alt.message}
                      </p>
                      <div style={{ fontSize: '11px', color: '#64748b', marginTop: '6px' }}>
                        Timestamp: {new Date(alt.timestamp).toLocaleTimeString()}
                      </div>
                    </div>
                  </div>

                  <button
                    onClick={() => handleResolve(alt.id)}
                    className="btn btn-secondary btn-sm"
                    title="Acknowledge Alert"
                  >
                    <Check size={14} />
                    <span>Acknowledge</span>
                  </button>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
