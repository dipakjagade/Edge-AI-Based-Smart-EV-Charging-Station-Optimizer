import React from 'react';
import { RefreshCw, Radio, HardDrive, ShieldCheck } from 'lucide-react';

export default function Header({ pageTitle, onRefresh, isRefreshing, demoMode = true, modelLoaded = true }) {
  return (
    <header className="topbar">
      <div>
        <h1 style={{ fontSize: '20px', fontWeight: 700, color: '#f8fafc' }}>{pageTitle}</h1>
        <p style={{ fontSize: '12px', color: '#64748b' }}>Edge AI EV Charging Hub &bull; 150 kW Transformer Management</p>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
        {demoMode && (
          <div className="demo-badge">
            <Radio size={12} />
            <span>Simulated Telemetry</span>
          </div>
        )}

        <div className={`badge ${modelLoaded ? 'badge-emerald' : 'badge-amber'}`}>
          <ShieldCheck size={14} />
          <span>{modelLoaded ? 'Edge AI Active' : 'Fallback Heuristic'}</span>
        </div>

        <button 
          onClick={onRefresh} 
          className="btn btn-secondary btn-sm"
          title="Refresh Data"
        >
          <RefreshCw size={14} className={isRefreshing ? 'animate-spin' : ''} />
          <span>Sync</span>
        </button>
      </div>
    </header>
  );
}
