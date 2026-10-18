import React, { useState, useEffect } from 'react';
import { 
  Plus, 
  Trash2, 
  Edit3, 
  Clock, 
  Zap, 
  AlertCircle, 
  CheckCircle, 
  Search, 
  Filter 
} from 'lucide-react';
import { SessionsAPI, OptimizerAPI } from '../services/api';
import { StatusBadge, Modal } from '../components/MetricCard';

export default function SessionsPage() {
  const [sessions, setSessions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filterStatus, setFilterStatus] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');
  
  // Modal states
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isEditMode, setIsEditMode] = useState(false);
  const [editingId, setEditingId] = useState(null);
  
  // Form state
  const [formData, setFormData] = useState({
    session_id: '',
    charger_id: 'EVSE-01',
    arrival_time: '',
    departure_time: '',
    max_power_kw: 22.0,
    requested_energy_kwh: 35.0,
    initial_soc_pct: 25.0,
    battery_capacity_kwh: 75.0,
    priority: 3,
    status: 'active'
  });
  const [formError, setFormError] = useState(null);

  const fetchSessions = async () => {
    try {
      setLoading(true);
      const data = await SessionsAPI.list(filterStatus === 'all' ? null : filterStatus);
      setSessions(data);
    } catch (err) {
      console.error('Error fetching sessions:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSessions();
  }, [filterStatus]);

  const handleOpenAddModal = () => {
    const now = new Date();
    const inThreeHours = new Date(now.getTime() + 3 * 3600 * 1000);
    
    // Format to YYYY-MM-DDTHH:mm
    const toISO = (d) => d.toISOString().slice(0, 16);

    setFormData({
      session_id: `EV-SIM-${Math.floor(100 + Math.random() * 900)}`,
      charger_id: `EVSE-0${Math.floor(1 + Math.random() * 8)}`,
      arrival_time: toISO(now),
      departure_time: toISO(inThreeHours),
      max_power_kw: 22.0,
      requested_energy_kwh: 35.0,
      initial_soc_pct: 25.0,
      battery_capacity_kwh: 75.0,
      priority: 3,
      status: 'active'
    });
    setIsEditMode(false);
    setFormError(null);
    setIsModalOpen(true);
  };

  const handleOpenEditModal = (s) => {
    setFormData({
      session_id: s.session_id,
      charger_id: s.charger_id,
      arrival_time: s.arrival_time.slice(0, 16),
      departure_time: s.departure_time.slice(0, 16),
      max_power_kw: s.max_power_kw,
      requested_energy_kwh: s.requested_energy_kwh,
      initial_soc_pct: s.initial_soc_pct || 20.0,
      battery_capacity_kwh: s.battery_capacity_kwh || 75.0,
      priority: s.priority,
      status: s.status
    });
    setEditingId(s.session_id);
    setIsEditMode(true);
    setFormError(null);
    setIsModalOpen(true);
  };

  const handleFormSubmit = async (e) => {
    e.preventDefault();
    setFormError(null);

    // Validate timestamps
    const arr = new Date(formData.arrival_time);
    const dep = new Date(formData.departure_time);
    if (dep <= arr) {
      setFormError('Departure deadline must be chronologically after arrival time.');
      return;
    }

    try {
      if (isEditMode) {
        await SessionsAPI.update(editingId, {
          charger_id: formData.charger_id,
          departure_time: formData.departure_time,
          max_power_kw: parseFloat(formData.max_power_kw),
          requested_energy_kwh: parseFloat(formData.requested_energy_kwh),
          priority: parseInt(formData.priority),
          status: formData.status
        });
      } else {
        await SessionsAPI.create({
          ...formData,
          max_power_kw: parseFloat(formData.max_power_kw),
          requested_energy_kwh: parseFloat(formData.requested_energy_kwh),
          initial_soc_pct: parseFloat(formData.initial_soc_pct),
          battery_capacity_kwh: parseFloat(formData.battery_capacity_kwh),
          priority: parseInt(formData.priority)
        });
      }
      setIsModalOpen(false);
      fetchSessions();
    } catch (err) {
      setFormError(err.message || 'Failed to save session');
    }
  };

  const handleDeleteSession = async (sessionId) => {
    if (window.confirm(`Are you sure you want to remove session ${sessionId}?`)) {
      try {
        await SessionsAPI.delete(sessionId);
        fetchSessions();
      } catch (err) {
        alert(`Delete failed: ${err.message}`);
      }
    }
  };

  const handleOptimizeActive = async () => {
    try {
      await OptimizerAPI.optimizeActive('water_filling', 150.0);
      alert('Power allocation optimizer completed. Vehicle rates updated.');
      fetchSessions();
    } catch (err) {
      alert(`Optimization failed: ${err.message}`);
    }
  };

  const filteredSessions = sessions.filter(s => {
    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      return s.session_id.toLowerCase().includes(q) || s.charger_id.toLowerCase().includes(q);
    }
    return true;
  });

  return (
    <div>
      {/* Header Controls */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px', flexWrap: 'wrap', gap: '16px' }}>
        <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
          <div style={{ position: 'relative', width: '240px' }}>
            <Search size={16} style={{ position: 'absolute', left: '12px', top: '12px', color: '#64748b' }} />
            <input
              type="text"
              placeholder="Search session or stall..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="form-control"
              style={{ paddingLeft: '36px' }}
            />
          </div>

          <div style={{ display: 'flex', gap: '6px' }}>
            {['all', 'active', 'completed'].map((st) => (
              <button
                key={st}
                onClick={() => setFilterStatus(st)}
                className={`btn btn-sm ${filterStatus === st ? 'btn-primary' : 'btn-secondary'}`}
                style={{ textTransform: 'capitalize' }}
              >
                {st}
              </button>
            ))}
          </div>
        </div>

        <div style={{ display: 'flex', gap: '12px' }}>
          <button onClick={handleOptimizeActive} className="btn btn-secondary">
            <Zap size={16} color="#10b981" />
            <span>Optimize Active Stalls</span>
          </button>
          <button onClick={handleOpenAddModal} className="btn btn-primary">
            <Plus size={16} />
            <span>New EV Session</span>
          </button>
        </div>
      </div>

      {/* Sessions Table */}
      <div className="glass-card">
        <div className="table-container">
          <table className="modern-table">
            <thead>
              <tr>
                <th>Vehicle / Session ID</th>
                <th>Charger Stall</th>
                <th>Arrival Time</th>
                <th>Departure Deadline</th>
                <th>Battery SOC</th>
                <th>Requested Energy</th>
                <th>Allocated Rate</th>
                <th>Required Min kW</th>
                <th>Priority</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filteredSessions.length === 0 ? (
                <tr>
                  <td colSpan={11} style={{ textAlign: 'center', color: '#64748b', padding: '40px' }}>
                    No charging sessions found matching current filter.
                  </td>
                </tr>
              ) : (
                filteredSessions.map((s) => (
                  <tr key={s.session_id}>
                    <td style={{ fontWeight: 600, fontFamily: 'monospace' }}>
                      {s.session_id}
                    </td>
                    <td>
                      <span className="badge badge-purple">{s.charger_id}</span>
                    </td>
                    <td style={{ color: '#94a3b8' }}>
                      {new Date(s.arrival_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </td>
                    <td style={{ color: '#94a3b8' }}>
                      <Clock size={12} style={{ display: 'inline', marginRight: '4px' }} />
                      {new Date(s.departure_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </td>
                    <td>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                        <div style={{ width: '45px', height: '6px', background: '#334155', borderRadius: '3px', overflow: 'hidden' }}>
                          <div style={{ width: `${s.current_soc_pct || 25}%`, height: '100%', background: '#10b981' }} />
                        </div>
                        <span style={{ fontSize: '11px' }}>{s.current_soc_pct ? `${s.current_soc_pct}%` : 'N/A'}</span>
                      </div>
                    </td>
                    <td>{s.requested_energy_kwh} kWh</td>
                    <td style={{ fontWeight: 700, color: '#34d399' }}>
                      {s.allocated_power_kw} kW
                    </td>
                    <td style={{ color: s.is_achievable ? '#94a3b8' : '#f87171' }}>
                      {s.minimum_required_power_kw} kW
                    </td>
                    <td>
                      <span className={`badge ${s.priority >= 4 ? 'badge-rose' : (s.priority === 3 ? 'badge-cyan' : 'badge-amber')}`}>
                        P{s.priority}
                      </span>
                    </td>
                    <td>
                      <StatusBadge status={s.status} />
                    </td>
                    <td>
                      <div style={{ display: 'flex', gap: '8px' }}>
                        <button 
                          onClick={() => handleOpenEditModal(s)}
                          className="btn btn-secondary btn-sm"
                          title="Edit Session"
                        >
                          <Edit3 size={13} />
                        </button>
                        <button 
                          onClick={() => handleDeleteSession(s.session_id)}
                          className="btn btn-danger btn-sm"
                          title="Delete Session"
                        >
                          <Trash2 size={13} />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Add / Edit Modal */}
      <Modal 
        isOpen={isModalOpen} 
        onClose={() => setIsModalOpen(false)}
        title={isEditMode ? `Edit EV Session: ${formData.session_id}` : 'Create Simulated EV Session'}
      >
        <form onSubmit={handleFormSubmit}>
          {formError && (
            <div className="alert-banner alert-danger" style={{ marginBottom: '16px' }}>
              <AlertCircle size={16} />
              <span>{formError}</span>
            </div>
          )}

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
            <div className="form-group">
              <label className="form-label">Session / Vehicle ID</label>
              <input
                type="text"
                disabled={isEditMode}
                required
                value={formData.session_id}
                onChange={(e) => setFormData({ ...formData, session_id: e.target.value })}
                className="form-control"
              />
            </div>

            <div className="form-group">
              <label className="form-label">Charger Stall</label>
              <select
                value={formData.charger_id}
                onChange={(e) => setFormData({ ...formData, charger_id: e.target.value })}
                className="form-control"
              >
                {[...Array(10)].map((_, i) => (
                  <option key={i} value={`EVSE-0${i + 1}`}>EVSE-0{i + 1}</option>
                ))}
              </select>
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
            <div className="form-group">
              <label className="form-label">Arrival Time</label>
              <input
                type="datetime-local"
                required
                value={formData.arrival_time}
                onChange={(e) => setFormData({ ...formData, arrival_time: e.target.value })}
                className="form-control"
              />
            </div>

            <div className="form-group">
              <label className="form-label">Departure Deadline</label>
              <input
                type="datetime-local"
                required
                value={formData.departure_time}
                onChange={(e) => setFormData({ ...formData, departure_time: e.target.value })}
                className="form-control"
              />
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '16px' }}>
            <div className="form-group">
              <label className="form-label">Max Power (kW)</label>
              <input
                type="number"
                min="3.7"
                max="350"
                step="0.1"
                required
                value={formData.max_power_kw}
                onChange={(e) => setFormData({ ...formData, max_power_kw: e.target.value })}
                className="form-control"
              />
            </div>

            <div className="form-group">
              <label className="form-label">Target Energy (kWh)</label>
              <input
                type="number"
                min="1"
                max="200"
                step="0.5"
                required
                value={formData.requested_energy_kwh}
                onChange={(e) => setFormData({ ...formData, requested_energy_kwh: e.target.value })}
                className="form-control"
              />
            </div>

            <div className="form-group">
              <label className="form-label">Initial SOC (%)</label>
              <input
                type="number"
                min="0"
                max="100"
                value={formData.initial_soc_pct}
                onChange={(e) => setFormData({ ...formData, initial_soc_pct: e.target.value })}
                className="form-control"
              />
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
            <div className="form-group">
              <label className="form-label">Scheduling Priority</label>
              <select
                value={formData.priority}
                onChange={(e) => setFormData({ ...formData, priority: e.target.value })}
                className="form-control"
              >
                <option value={1}>P1 - Lowest / Opportunistic</option>
                <option value={2}>P2 - Standard Daily</option>
                <option value={3}>P3 - Regular Commuter</option>
                <option value={4}>P4 - High Priority</option>
                <option value={5}>P5 - Emergency / VIP Fast</option>
              </select>
            </div>

            <div className="form-group">
              <label className="form-label">Session Status</label>
              <select
                value={formData.status}
                onChange={(e) => setFormData({ ...formData, status: e.target.value })}
                className="form-control"
              >
                <option value="active">Active (Charging)</option>
                <option value="pending">Pending</option>
                <option value="completed">Completed</option>
                <option value="cancelled">Cancelled</option>
              </select>
            </div>
          </div>

          <div className="modal-footer">
            <button type="button" onClick={() => setIsModalOpen(false)} className="btn btn-secondary">
              Cancel
            </button>
            <button type="submit" className="btn btn-primary">
              {isEditMode ? 'Update Session' : 'Save Session'}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
