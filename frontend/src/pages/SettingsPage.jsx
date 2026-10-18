import React, { useState, useEffect } from 'react';
import { 
  Settings, 
  Save, 
  Zap, 
  DollarSign, 
  CheckCircle, 
  ShieldCheck, 
  Sliders 
} from 'lucide-react';
import { SettingsAPI } from '../services/api';

export default function SettingsPage() {
  const [settings, setSettings] = useState({
    station_name: 'Antigravity Edge EV Hub #1',
    station_power_limit_kw: 150.0,
    total_chargers: 10,
    default_charger_limit_kw: 22.0,
    currency: 'USD',
    demo_mode: true,
    edge_mode: true,
    coincident_peak_penalty_usd_per_kw: 12.50
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [savedSuccess, setSavedSuccess] = useState(false);

  const fetchSettings = async () => {
    try {
      setLoading(true);
      const data = await SettingsAPI.get();
      setSettings(data);
    } catch (err) {
      console.error('Failed to load settings:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSettings();
  }, []);

  const handleSave = async (e) => {
    e.preventDefault();
    try {
      setSaving(true);
      setSavedSuccess(false);
      const updated = await SettingsAPI.update({
        ...settings,
        station_power_limit_kw: parseFloat(settings.station_power_limit_kw),
        total_chargers: parseInt(settings.total_chargers),
        default_charger_limit_kw: parseFloat(settings.default_charger_limit_kw),
        coincident_peak_penalty_usd_per_kw: parseFloat(settings.coincident_peak_penalty_usd_per_kw)
      });
      setSettings(updated);
      setSavedSuccess(true);
      setTimeout(() => setSavedSuccess(false), 4000);
    } catch (err) {
      alert(`Save failed: ${err.message}`);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div>
      {/* Header Info */}
      <div style={{ marginBottom: '24px' }}>
        <p style={{ fontSize: '13px', color: '#94a3b8' }}>
          Configure hub electrical parameters, individual EVSE limits, utility tariff rates, and edge operating modes. Changes take effect immediately in the runtime optimizer.
        </p>
      </div>

      <form onSubmit={handleSave}>
        <div className="glass-card" style={{ marginBottom: '24px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
            <h3 style={{ fontSize: '16px', fontWeight: 600 }}>Station & Electrical Transformer Configuration</h3>
            <span className="badge badge-emerald">Hardware Profile</span>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '20px' }}>
            <div className="form-group">
              <label className="form-label">Station Facility Name</label>
              <input
                type="text"
                required
                value={settings.station_name}
                onChange={(e) => setSettings({ ...settings, station_name: e.target.value })}
                className="form-control"
              />
            </div>

            <div className="form-group">
              <label className="form-label">Station Transformer Rating Limit (kW)</label>
              <input
                type="number"
                min="50"
                max="2000"
                step="10"
                required
                value={settings.station_power_limit_kw}
                onChange={(e) => setSettings({ ...settings, station_power_limit_kw: e.target.value })}
                className="form-control"
              />
            </div>

            <div className="form-group">
              <label className="form-label">Total EVSE Charger Stalls</label>
              <input
                type="number"
                min="1"
                max="100"
                required
                value={settings.total_chargers}
                onChange={(e) => setSettings({ ...settings, total_chargers: e.target.value })}
                className="form-control"
              />
            </div>

            <div className="form-group">
              <label className="form-label">Default EVSE Stall Rating (kW)</label>
              <input
                type="number"
                min="3.7"
                max="350"
                step="0.1"
                required
                value={settings.default_charger_limit_kw}
                onChange={(e) => setSettings({ ...settings, default_charger_limit_kw: e.target.value })}
                className="form-control"
              />
            </div>
          </div>
        </div>

        {/* Tariffs and Penalties Card */}
        <div className="glass-card" style={{ marginBottom: '24px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
            <h3 style={{ fontSize: '16px', fontWeight: 600 }}>Utility Tariff & Demand Charge Parameters</h3>
            <span className="badge badge-purple">Rate Structure</span>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '20px' }}>
            <div className="form-group">
              <label className="form-label">Peak Demand Charge Penalty ($/kW)</label>
              <input
                type="number"
                min="0"
                max="50"
                step="0.5"
                value={settings.coincident_peak_penalty_usd_per_kw}
                onChange={(e) => setSettings({ ...settings, coincident_peak_penalty_usd_per_kw: e.target.value })}
                className="form-control"
              />
            </div>

            <div className="form-group">
              <label className="form-label">Currency Symbol</label>
              <input
                type="text"
                value={settings.currency}
                onChange={(e) => setSettings({ ...settings, currency: e.target.value })}
                className="form-control"
              />
            </div>

            <div className="form-group">
              <label className="form-label">Operating Environment</label>
              <div style={{ display: 'flex', gap: '16px', paddingTop: '10px' }}>
                <label style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '13px', cursor: 'pointer' }}>
                  <input
                    type="checkbox"
                    checked={settings.demo_mode}
                    onChange={(e) => setSettings({ ...settings, demo_mode: e.target.checked })}
                    style={{ accentColor: '#10b981' }}
                  />
                  <span>Simulated Demo Mode</span>
                </label>

                <label style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '13px', cursor: 'pointer' }}>
                  <input
                    type="checkbox"
                    checked={settings.edge_mode}
                    onChange={(e) => setSettings({ ...settings, edge_mode: e.target.checked })}
                    style={{ accentColor: '#10b981' }}
                  />
                  <span>Edge Computer Mode</span>
                </label>
              </div>
            </div>
          </div>
        </div>

        {/* Action Button & Confirmation */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: '16px' }}>
          {savedSuccess && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#34d399', fontSize: '13px' }}>
              <CheckCircle size={16} />
              <span>Settings saved and applied to edge runtime successfully!</span>
            </div>
          )}

          <button type="submit" disabled={saving} className="btn btn-primary">
            <Save size={16} />
            <span>{saving ? 'Saving...' : 'Save Configuration'}</span>
          </button>
        </div>
      </form>
    </div>
  );
}
