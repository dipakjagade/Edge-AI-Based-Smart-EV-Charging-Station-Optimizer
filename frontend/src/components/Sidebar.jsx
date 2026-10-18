import React from 'react';
import { 
  LayoutDashboard, 
  BatteryCharging, 
  Cpu, 
  Zap, 
  Database, 
  BrainCircuit, 
  TrendingDown, 
  BellRing, 
  Settings, 
  BookOpen 
} from 'lucide-react';

const navItems = [
  { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { id: 'sessions', label: 'EV Sessions', icon: BatteryCharging },
  { id: 'prediction', label: 'Demand Prediction', icon: Cpu },
  { id: 'optimizer', label: 'Smart Optimizer', icon: Zap },
  { id: 'datasets', label: 'Dataset Management', icon: Database },
  { id: 'models', label: 'Model Training', icon: BrainCircuit },
  { id: 'analytics', label: 'Cost & Analytics', icon: TrendingDown },
  { id: 'alerts', label: 'Alerts & Health', icon: BellRing },
  { id: 'settings', label: 'Settings', icon: Settings },
  { id: 'docs', label: 'Documentation', icon: BookOpen },
];

export default function Sidebar({ activePage, setActivePage }) {
  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <div className="logo-badge">
          <Zap size={22} />
        </div>
        <div>
          <h2 style={{ fontSize: '15px', fontWeight: 700, letterSpacing: '-0.02em', color: '#fff' }}>Edge EV Hub</h2>
          <span style={{ fontSize: '11px', color: '#94a3b8' }}>Smart Power Optimizer</span>
        </div>
      </div>

      <nav className="sidebar-nav">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = activePage === item.id;
          return (
            <button
              key={item.id}
              onClick={() => setActivePage(item.id)}
              className={`nav-item ${isActive ? 'active' : ''}`}
              style={{ background: 'none', border: 'none', width: '100%', textAlign: 'left' }}
            >
              <Icon size={18} />
              <span>{item.label}</span>
            </button>
          );
        })}
      </nav>

      <div className="sidebar-footer">
        <div className="edge-badge">
          <div className="pulse-dot"></div>
          <div>
            <div style={{ fontWeight: 600, fontSize: '11px' }}>EDGE INFERENCE</div>
            <div style={{ fontSize: '10px', color: '#6ee7b7' }}>Local Random Forest</div>
          </div>
        </div>
      </div>
    </aside>
  );
}
