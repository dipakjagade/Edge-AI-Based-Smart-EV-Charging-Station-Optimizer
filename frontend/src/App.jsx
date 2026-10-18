import React, { useState, useEffect } from 'react';
import Sidebar from './components/Sidebar';
import Header from './components/Header';
import DashboardPage from './pages/DashboardPage';
import SessionsPage from './pages/SessionsPage';
import PredictionPage from './pages/PredictionPage';
import OptimizerPage from './pages/OptimizerPage';
import DatasetsPage from './pages/DatasetsPage';
import ModelTrainingPage from './pages/ModelTrainingPage';
import AnalyticsPage from './pages/AnalyticsPage';
import AlertsHealthPage from './pages/AlertsHealthPage';
import SettingsPage from './pages/SettingsPage';
import DocumentationPage from './pages/DocumentationPage';
import { DashboardAPI } from './services/api';

const pageTitles = {
  dashboard: 'Station Overview & Demand Dashboard',
  sessions: 'EV Charging Session Management',
  prediction: 'Edge AI Demand Prediction Workstation',
  optimizer: 'Constrained Power Allocation Optimizer',
  datasets: 'Dataset Ingestion & Quality Audit',
  models: 'Model Training & Chronological Evaluation',
  analytics: 'TOU Electricity Tariff & Cost Analytics',
  alerts: 'System Diagnostics & Health Feed',
  settings: 'Hub & Transformer Settings',
  docs: 'Architecture & Edge Deployment Documentation'
};

export default function App() {
  const [activePage, setActivePage] = useState('dashboard');
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [healthData, setHealthData] = useState(null);

  const fetchHealth = async () => {
    try {
      setIsRefreshing(true);
      const data = await DashboardAPI.getHealth();
      setHealthData(data);
    } catch (err) {
      console.error('Health check failed:', err);
    } finally {
      setTimeout(() => setIsRefreshing(false), 500);
    }
  };

  useEffect(() => {
    fetchHealth();
  }, [activePage]);

  const renderActivePage = () => {
    switch (activePage) {
      case 'dashboard':
        return <DashboardPage setActivePage={setActivePage} />;
      case 'sessions':
        return <SessionsPage />;
      case 'prediction':
        return <PredictionPage />;
      case 'optimizer':
        return <OptimizerPage />;
      case 'datasets':
        return <DatasetsPage />;
      case 'models':
        return <ModelTrainingPage />;
      case 'analytics':
        return <AnalyticsPage />;
      case 'alerts':
        return <AlertsHealthPage />;
      case 'settings':
        return <SettingsPage />;
      case 'docs':
        return <DocumentationPage />;
      default:
        return <DashboardPage setActivePage={setActivePage} />;
    }
  };

  return (
    <div className="app-container">
      <Sidebar activePage={activePage} setActivePage={setActivePage} />

      <div className="main-wrapper">
        <Header 
          pageTitle={pageTitles[activePage] || 'EV Station Optimizer'}
          onRefresh={fetchHealth}
          isRefreshing={isRefreshing}
          demoMode={true}
          modelLoaded={healthData?.model_loaded ?? true}
        />

        <main className="content-body">
          {renderActivePage()}
        </main>
      </div>
    </div>
  );
}
