import React, { useState, useEffect } from 'react';
import { 
  BrainCircuit, 
  Play, 
  CheckCircle, 
  BarChart2, 
  Clock, 
  Award, 
  TrendingUp, 
  ShieldCheck 
} from 'lucide-react';
import { 
  LineChart, 
  Line, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  Legend, 
  ResponsiveContainer, 
  BarChart, 
  Bar 
} from 'recharts';
import { ModelsAPI } from '../services/api';
import { MetricCard } from '../components/MetricCard';

export default function ModelTrainingPage() {
  const [status, setStatus] = useState(null);
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [training, setTraining] = useState(false);
  
  // Hyperparameters
  const [trees, setTrees] = useState(100);
  const [maxDepth, setMaxDepth] = useState(15);

  const fetchModelInfo = async () => {
    try {
      setLoading(true);
      const [st, mt] = await Promise.all([
        ModelsAPI.getStatus(),
        ModelsAPI.getMetrics().catch(() => null)
      ]);
      setStatus(st);
      setMetrics(mt);
    } catch (err) {
      console.error('Failed to load model info:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchModelInfo();
  }, []);

  const handleTrain = async () => {
    try {
      setTraining(true);
      await ModelsAPI.train(parseInt(trees), parseInt(maxDepth));
      alert('Training job started in the background. Polling for results...');
      
      // Poll every 3 seconds until completed
      const interval = setInterval(async () => {
        const st = await ModelsAPI.getStatus();
        setStatus(st);
        if (!st.is_training) {
          clearInterval(interval);
          setTraining(false);
          const mt = await ModelsAPI.getMetrics().catch(() => null);
          setMetrics(mt);
          alert('Model training and chronological evaluation completed successfully!');
        }
      }, 3000);
    } catch (err) {
      alert(`Training trigger failed: ${err.message}`);
      setTraining(false);
    }
  };

  // Prepare feature importances for chart
  const featureData = metrics?.feature_importances 
    ? Object.entries(metrics.feature_importances).map(([feat, imp]) => ({
        feature: feat.replace(/_/g, ' '),
        importance: Math.round(imp * 1000) / 10
      })).slice(0, 7)
    : [];

  // Prepare sample eval chart
  const evalChartData = metrics?.sample_eval_chart?.timestamps?.map((ts, idx) => ({
    time: ts.includes(' ') ? ts.split(' ')[1].slice(0, 5) : ts,
    Actual: metrics.sample_eval_chart.actual[idx],
    'Random Forest': metrics.sample_eval_chart.predicted[idx],
    'Naive Baseline': metrics.sample_eval_chart.baseline[idx]
  })) || [];

  return (
    <div>
      {/* Header Info */}
      <div style={{ marginBottom: '24px' }}>
        <p style={{ fontSize: '13px', color: '#94a3b8' }}>
          Train and evaluate the local Edge AI Random Forest Regressor. Uses strict chronological train/test splitting (80% train, 20% holdout) to prevent data leakage and evaluate real-world generalization against naive persistence baselines.
        </p>
      </div>

      {/* Training Trigger Card */}
      <div className="glass-card" style={{ marginBottom: '24px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px', flexWrap: 'wrap', gap: '16px' }}>
          <div>
            <h3 style={{ fontSize: '16px', fontWeight: 600 }}>Edge Model Configuration & Training</h3>
            <p style={{ fontSize: '12px', color: '#94a3b8' }}>Saved Artifact: <code>backend/saved_models/rf_demand_model.joblib</code></p>
          </div>
          <span className={`badge ${status?.model_loaded ? 'badge-emerald' : 'badge-amber'}`}>
            {status?.model_loaded ? 'Model Loaded & Active' : 'Model Absent (Fallback)'}
          </span>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px', alignItems: 'flex-end' }}>
          <div className="form-group" style={{ marginBottom: 0 }}>
            <label className="form-label">Number of Estimator Trees</label>
            <input
              type="number"
              min="20"
              max="200"
              step="10"
              value={trees}
              onChange={(e) => setTrees(e.target.value)}
              className="form-control"
            />
          </div>

          <div className="form-group" style={{ marginBottom: 0 }}>
            <label className="form-label">Max Tree Depth</label>
            <input
              type="number"
              min="4"
              max="25"
              value={maxDepth}
              onChange={(e) => setMaxDepth(e.target.value)}
              className="form-control"
            />
          </div>

          <div>
            <button
              onClick={handleTrain}
              disabled={training || status?.is_training}
              className="btn btn-primary"
              style={{ width: '100%', height: '42px' }}
            >
              <Play size={16} />
              <span>{training || status?.is_training ? 'Training Random Forest...' : 'Retrain AI Model'}</span>
            </button>
          </div>
        </div>
      </div>

      {/* Model Metrics Cards */}
      {metrics?.metrics && (
        <div className="metrics-grid">
          <MetricCard
            title="Random Forest MAE"
            value={metrics.metrics.rf_mae_kw}
            unit="kW"
            icon={Award}
            color="emerald"
            footerText={`vs. Baseline ${metrics.metrics.baseline_mae_kw} kW`}
            footerBadge={`${metrics.metrics.mae_improvement_pct}% Better`}
          />

          <MetricCard
            title="Root Mean Squared Error"
            value={metrics.metrics.rf_rmse_kw}
            unit="kW"
            icon={TrendingUp}
            color="cyan"
            footerText={`Baseline RMSE: ${metrics.metrics.baseline_rmse_kw} kW`}
            footerBadge="Holdout Test"
          />

          <MetricCard
            title="R-Squared Score (R²)"
            value={metrics.metrics.rf_r2}
            unit=""
            icon={CheckCircle}
            color="purple"
            footerText="Variance Explained"
            footerBadge="High Fit"
          />

          <MetricCard
            title="Holdout Evaluation Size"
            value={metrics.test_samples.toLocaleString()}
            unit="Samples"
            icon={Clock}
            color="amber"
            footerText={`${metrics.total_samples.toLocaleString()} Total Rows`}
            footerBadge="Chronological"
          />
        </div>
      )}

      {/* Actual vs Predicted Demand Evaluation Chart */}
      {evalChartData.length > 0 && (
        <div className="glass-card" style={{ marginBottom: '24px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
            <div>
              <h3 style={{ fontSize: '16px', fontWeight: 600 }}>Chronological Test Holdout: Actual vs. Predicted Demand</h3>
              <p style={{ fontSize: '12px', color: '#94a3b8' }}>Out-of-sample evaluation comparing model inferences against actual demand and naive baseline</p>
            </div>
            <span className="badge badge-emerald">Unseen Test Slice</span>
          </div>

          <div style={{ height: '340px', width: '100%' }}>
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={evalChartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                <XAxis dataKey="time" stroke="#64748b" fontSize={11} />
                <YAxis stroke="#64748b" fontSize={11} unit=" kW" domain={[0, 160]} />
                <Tooltip 
                  contentStyle={{ background: '#0f172a', borderColor: 'rgba(255,255,255,0.1)', borderRadius: '8px' }}
                  labelStyle={{ color: '#f8fafc', fontWeight: 600 }}
                />
                <Legend wrapperStyle={{ paddingTop: '10px' }} />
                <Line type="monotone" dataKey="Actual" stroke="#38bdf8" strokeWidth={2.5} dot={false} />
                <Line type="monotone" dataKey="Random Forest" stroke="#10b981" strokeWidth={2} dot={false} />
                <Line type="monotone" dataKey="Naive Baseline" stroke="#94a3b8" strokeDasharray="3 3" strokeWidth={1.5} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* Feature Importances */}
      {featureData.length > 0 && (
        <div className="glass-card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
            <div>
              <h3 style={{ fontSize: '16px', fontWeight: 600 }}>Top Feature Importances (Gini Impurity)</h3>
              <p style={{ fontSize: '12px', color: '#94a3b8' }}>Relative contribution of each predictor in Random Forest tree splits</p>
            </div>
            <span className="badge badge-purple">Feature Weights</span>
          </div>

          <div style={{ height: '260px', width: '100%' }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={featureData} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                <XAxis type="number" stroke="#64748b" fontSize={11} unit="%" />
                <YAxis dataKey="feature" type="category" stroke="#94a3b8" fontSize={11} width={180} />
                <Tooltip 
                  contentStyle={{ background: '#0f172a', borderColor: 'rgba(255,255,255,0.1)', borderRadius: '8px' }}
                  labelStyle={{ color: '#f8fafc', fontWeight: 600 }}
                  formatter={(val) => [`${val}%`, 'Importance']}
                />
                <Bar dataKey="importance" fill="#8b5cf6" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}
    </div>
  );
}
