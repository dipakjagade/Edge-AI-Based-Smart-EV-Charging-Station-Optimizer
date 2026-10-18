import React, { useState, useEffect } from 'react';
import { 
  Database, 
  Upload, 
  FileText, 
  CheckCircle, 
  AlertTriangle, 
  RefreshCw, 
  ShieldCheck, 
  Sparkles, 
  Table 
} from 'lucide-react';
import { DatasetsAPI } from '../services/api';
import { MetricCard } from '../components/MetricCard';

export default function DatasetsPage() {
  const [datasets, setDatasets] = useState([]);
  const [selectedDataset, setSelectedDataset] = useState(null);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [generating, setGenerating] = useState(false);

  const fetchDatasets = async () => {
    try {
      setLoading(true);
      const data = await DatasetsAPI.list();
      setDatasets(data);
      if (data.length > 0 && !selectedDataset) {
        setSelectedDataset(data[0]);
      }
    } catch (err) {
      console.error('Failed to load datasets:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDatasets();
  }, []);

  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    try {
      setUploading(true);
      const newDs = await DatasetsAPI.upload(file);
      alert(`Dataset "${file.name}" uploaded and validated successfully!`);
      await fetchDatasets();
      setSelectedDataset(newDs);
    } catch (err) {
      alert(`Upload failed: ${err.message}`);
    } finally {
      setUploading(false);
      e.target.value = null;
    }
  };

  const handleGenerateSynthetic = async () => {
    try {
      setGenerating(true);
      const res = await DatasetsAPI.generateSynthetic(90);
      alert(res.message);
      await fetchDatasets();
      setSelectedDataset(res.dataset);
    } catch (err) {
      alert(`Generation failed: ${err.message}`);
    } finally {
      setGenerating(false);
    }
  };

  const qr = selectedDataset?.quality_report;

  return (
    <div>
      {/* Header Info */}
      <div style={{ marginBottom: '24px' }}>
        <p style={{ fontSize: '13px', color: '#94a3b8' }}>
          Upload, parse, and evaluate EV charging telemetry datasets. The ingestion engine automatically validates timestamp continuities, checks missing fields, flags negative power anomalies, and calculates a data quality readiness score.
        </p>
      </div>

      {/* Upload and Generation Actions */}
      <div className="glass-card" style={{ marginBottom: '24px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px' }}>
          <div>
            <h3 style={{ fontSize: '16px', fontWeight: 600 }}>Dataset Ingestion & Benchmarking</h3>
            <p style={{ fontSize: '12px', color: '#94a3b8' }}>Supports standard time-series telemetry and Caltech/JPL ACN-Data format</p>
          </div>

          <div style={{ display: 'flex', gap: '12px' }}>
            <label className="btn btn-secondary" style={{ cursor: 'pointer' }}>
              <Upload size={16} />
              <span>{uploading ? 'Parsing CSV...' : 'Upload CSV Dataset'}</span>
              <input type="file" accept=".csv" onChange={handleFileUpload} style={{ display: 'none' }} />
            </label>

            <button 
              onClick={handleGenerateSynthetic} 
              disabled={generating}
              className="btn btn-primary"
            >
              <Sparkles size={16} />
              <span>{generating ? 'Simulating 90 Days...' : 'Generate Synthetic Benchmark'}</span>
            </button>
          </div>
        </div>
      </div>

      {/* Main Dataset Inspection */}
      <div className="two-col-grid">
        {/* Dataset Selector List */}
        <div className="glass-card">
          <h3 style={{ fontSize: '16px', fontWeight: 600, marginBottom: '16px' }}>Available Datasets</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {datasets.map((d) => {
              const isSelected = selectedDataset?.id === d.id;
              return (
                <div
                  key={d.id}
                  onClick={() => setSelectedDataset(d)}
                  style={{
                    padding: '14px',
                    borderRadius: '10px',
                    border: `1px solid ${isSelected ? 'var(--accent-emerald)' : 'var(--border-color)'}`,
                    background: isSelected ? 'rgba(16, 185, 129, 0.08)' : 'rgba(15, 23, 42, 0.4)',
                    cursor: 'pointer',
                    transition: 'all 0.2s ease'
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
                    <div style={{ fontWeight: 600, fontSize: '13px', color: isSelected ? '#34d399' : '#f8fafc' }}>
                      {d.filename}
                    </div>
                    <span className="badge badge-purple">{d.quality_report.detected_format}</span>
                  </div>
                  <div style={{ display: 'flex', gap: '12px', fontSize: '11px', color: '#94a3b8' }}>
                    <span>{d.row_count.toLocaleString()} rows</span>
                    <span>&bull;</span>
                    <span>{d.column_count} columns</span>
                    <span>&bull;</span>
                    <span style={{ color: d.quality_report.quality_score_pct >= 90 ? '#34d399' : '#fbbf24' }}>
                      Score: {d.quality_report.quality_score_pct}%
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Selected Dataset Quality Report */}
        {selectedDataset && qr ? (
          <div className="glass-card">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <h3 style={{ fontSize: '16px', fontWeight: 600 }}>Data Quality Audit Report</h3>
              <span className={`badge ${qr.quality_score_pct >= 90 ? 'badge-emerald' : 'badge-amber'}`}>
                Quality Score: {qr.quality_score_pct}%
              </span>
            </div>

            <div className="metrics-grid" style={{ gridTemplateColumns: 'repeat(2, 1fr)', gap: '12px', marginBottom: '16px' }}>
              <div style={{ background: 'rgba(15, 23, 42, 0.5)', padding: '12px', borderRadius: '8px' }}>
                <span style={{ fontSize: '11px', color: '#94a3b8' }}>Detected Format</span>
                <div style={{ fontSize: '14px', fontWeight: 700, marginTop: '2px', textTransform: 'uppercase', color: '#38bdf8' }}>
                  {qr.detected_format}
                </div>
              </div>

              <div style={{ background: 'rgba(15, 23, 42, 0.5)', padding: '12px', borderRadius: '8px' }}>
                <span style={{ fontSize: '11px', color: '#94a3b8' }}>Missing Values</span>
                <div style={{ fontSize: '14px', fontWeight: 700, marginTop: '2px' }}>
                  {qr.missing_values_count} ({qr.missing_percentage}%)
                </div>
              </div>

              <div style={{ background: 'rgba(15, 23, 42, 0.5)', padding: '12px', borderRadius: '8px' }}>
                <span style={{ fontSize: '11px', color: '#94a3b8' }}>Duplicate Rows</span>
                <div style={{ fontSize: '14px', fontWeight: 700, marginTop: '2px' }}>
                  {qr.duplicate_rows_count}
                </div>
              </div>

              <div style={{ background: 'rgba(15, 23, 42, 0.5)', padding: '12px', borderRadius: '8px' }}>
                <span style={{ fontSize: '11px', color: '#94a3b8' }}>Negative Anomaly Values</span>
                <div style={{ fontSize: '14px', fontWeight: 700, marginTop: '2px', color: qr.negative_values_found > 0 ? '#f87171' : '#34d399' }}>
                  {qr.negative_values_found}
                </div>
              </div>
            </div>

            <div style={{ marginBottom: '16px' }}>
              <div style={{ fontSize: '12px', fontWeight: 600, color: '#94a3b8', marginBottom: '8px' }}>Validation Checks:</div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '12px' }}>
                  {qr.is_valid_for_training ? <CheckCircle size={14} color="#10b981" /> : <AlertTriangle size={14} color="#f59e0b" />}
                  <span>ML Model Training Compatibility: <strong>{qr.is_valid_for_training ? 'Verified' : 'Adjustments Required'}</strong></span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '12px' }}>
                  {qr.is_valid_for_scheduling ? <CheckCircle size={14} color="#10b981" /> : <AlertTriangle size={14} color="#f59e0b" />}
                  <span>Smart Scheduling Energy Inputs: <strong>{qr.is_valid_for_scheduling ? 'Present' : 'Not Detected'}</strong></span>
                </div>
              </div>
            </div>

            {qr.warnings.length > 0 && (
              <div className="alert-banner alert-warning" style={{ fontSize: '12px', padding: '10px 14px' }}>
                <AlertTriangle size={16} />
                <div>
                  {qr.warnings.map((w, idx) => (
                    <div key={idx}>{w}</div>
                  ))}
                </div>
              </div>
            )}
          </div>
        ) : null}
      </div>

      {/* Data Preview Table */}
      {qr?.preview_rows?.length > 0 && (
        <div className="glass-card" style={{ marginTop: '24px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
            <h3 style={{ fontSize: '16px', fontWeight: 600 }}>Raw Data Sample Preview (First 5 Rows)</h3>
            <span className="badge badge-cyan">{selectedDataset?.filename}</span>
          </div>

          <div className="table-container">
            <table className="modern-table">
              <thead>
                <tr>
                  {Object.keys(qr.preview_rows[0]).map((col) => (
                    <th key={col}>{col}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {qr.preview_rows.map((row, idx) => (
                  <tr key={idx}>
                    {Object.values(row).map((val, cidx) => (
                      <td key={cidx} style={{ fontFamily: typeof val === 'number' ? 'monospace' : 'inherit' }}>
                        {String(val)}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
