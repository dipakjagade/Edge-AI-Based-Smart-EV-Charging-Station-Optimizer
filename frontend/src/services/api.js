import axios from 'axios';

const api = axios.create({
  baseURL: '',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json'
  }
});

// Response interceptor for clear errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    const errorMsg = error.response?.data?.detail || error.message || 'Network request failed';
    console.error('[API Error]:', errorMsg);
    return Promise.reject(new Error(errorMsg));
  }
);

export const DashboardAPI = {
  getSummary: () => api.get('/api/dashboard/summary').then(res => res.data),
  getHealth: () => api.get('/health').then(res => res.data)
};

export const SessionsAPI = {
  list: (status) => api.get('/api/sessions', { params: { status } }).then(res => res.data),
  get: (id) => api.get(`/api/sessions/${id}`).then(res => res.data),
  create: (data) => api.post('/api/sessions', data).then(res => res.data),
  update: (id, data) => api.put(`/api/sessions/${id}`, data).then(res => res.data),
  delete: (id) => api.delete(`/api/sessions/${id}`).then(res => res.data)
};

export const PredictionAPI = {
  predict: (data) => api.post('/api/predict', data).then(res => res.data),
  getHistory: (limit = 20) => api.get('/api/predictions', { params: { limit } }).then(res => res.data),
  getById: (id) => api.get(`/api/predictions/${id}`).then(res => res.data)
};

export const OptimizerAPI = {
  optimize: (data) => api.post('/api/optimize', data).then(res => res.data),
  optimizeActive: (mode = 'water_filling', powerLimit = 150.0) => 
    api.post('/api/optimize/active-sessions', null, { params: { mode, station_power_limit_kw: powerLimit } }).then(res => res.data),
  getHistory: (limit = 20) => api.get('/api/optimizations', { params: { limit } }).then(res => res.data),
  getById: (id) => api.get(`/api/optimizations/${id}`).then(res => res.data)
};

export const DatasetsAPI = {
  list: () => api.get('/api/datasets').then(res => res.data),
  get: (id) => api.get(`/api/datasets/${id}`).then(res => res.data),
  upload: (file) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post('/api/datasets/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    }).then(res => res.data);
  },
  generateSynthetic: (days = 90) => 
    api.post('/api/datasets/generate-synthetic', null, { params: { days } }).then(res => res.data)
};

export const ModelsAPI = {
  getStatus: () => api.get('/api/models/status').then(res => res.data),
  getMetrics: () => api.get('/api/models/metrics').then(res => res.data),
  train: (estimators = 50, depth = 12, csvFile = 'synthetic_ev_charging_data.csv') =>
    api.post('/api/models/train', null, { params: { estimators, depth, csv_file: csvFile } }).then(res => res.data)
};

export const AnalyticsAPI = {
  getDemand: (days = 7) => api.get('/api/analytics/demand', { params: { days } }).then(res => res.data),
  getCost: (energyKwh = 350.0, stationLimit = 150.0) => 
    api.get('/api/analytics/cost', { params: { energy_kwh: energyKwh, station_limit_kw: stationLimit } }).then(res => res.data)
};

export const AlertsAPI = {
  list: () => api.get('/api/alerts').then(res => res.data),
  resolve: (id) => api.post(`/api/alerts/${id}/resolve`).then(res => res.data)
};

export const SettingsAPI = {
  get: () => api.get('/api/settings').then(res => res.data),
  update: (data) => api.post('/api/settings', data).then(res => res.data)
};

export default api;
