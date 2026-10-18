import React from 'react';

export function MetricCard({ title, value, unit, icon: Icon, footerText, footerBadge, color = 'emerald' }) {
  const colorMap = {
    emerald: { glow: 'rgba(16, 185, 129, 0.15)', text: '#34d399' },
    cyan: { glow: 'rgba(6, 182, 212, 0.15)', text: '#38bdf8' },
    amber: { glow: 'rgba(245, 158, 11, 0.15)', text: '#fbbf24' },
    rose: { glow: 'rgba(239, 68, 68, 0.15)', text: '#f87171' },
    purple: { glow: 'rgba(139, 92, 246, 0.15)', text: '#c084fc' }
  };

  const theme = colorMap[color] || colorMap.emerald;

  return (
    <div className="metric-card">
      <div className="metric-header">
        <span>{title}</span>
        {Icon && (
          <div style={{
            width: '32px',
            height: '32px',
            borderRadius: '8px',
            background: theme.glow,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: theme.text
          }}>
            <Icon size={18} />
          </div>
        )}
      </div>

      <div className="metric-value">
        {value}
        {unit && <span className="metric-unit">{unit}</span>}
      </div>

      {(footerText || footerBadge) && (
        <div className="metric-footer">
          {footerBadge && (
            <span className={`badge badge-${color}`}>
              {footerBadge}
            </span>
          )}
          {footerText && (
            <span style={{ color: '#94a3b8' }}>{footerText}</span>
          )}
        </div>
      )}
    </div>
  );
}

export function StatusBadge({ status }) {
  const norm = String(status).toLowerCase();
  
  if (norm === 'active' || norm === 'feasible' || norm === 'healthy' || norm === 'connected') {
    return <span className="badge badge-emerald">{status}</span>;
  }
  if (norm === 'infeasible' || norm === 'critical' || norm === 'overload' || norm === 'failed') {
    return <span className="badge badge-rose">{status}</span>;
  }
  if (norm === 'warning' || norm === 'degraded' || norm === 'throttled') {
    return <span className="badge badge-amber">{status}</span>;
  }
  if (norm === 'completed' || norm === 'info') {
    return <span className="badge badge-cyan">{status}</span>;
  }
  return <span className="badge badge-purple">{status}</span>;
}

export function Modal({ isOpen, onClose, title, children }) {
  if (!isOpen) return null;
  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h3 style={{ fontSize: '18px', fontWeight: 600 }}>{title}</h3>
          <button 
            onClick={onClose} 
            style={{ background: 'none', border: 'none', color: '#94a3b8', fontSize: '20px', cursor: 'pointer' }}
          >
            &times;
          </button>
        </div>
        <div>{children}</div>
      </div>
    </div>
  );
}
