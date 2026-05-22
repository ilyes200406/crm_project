import { api } from '../../../services/axios';
import axios from 'axios';

const BASE = '/leads';
const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api';

// Public client — no auth headers
const publicClient = axios.create({
  baseURL: BASE_URL,
  timeout: 15_000,
  headers: { 'Content-Type': 'application/json' },
});

export const leadsApi = {
  // Internal (auth required)
  getAll:          (params = {}) => api.get(`${BASE}/`, { params }),
  getById:         (id)          => api.get(`${BASE}/${id}/`),
  prendreEnCharge: (id)          => api.post(`${BASE}/${id}/prendre-en-charge/`),
  convertir:       (id, data)    => api.post(`${BASE}/${id}/convertir/`, data),
  annuler:         (id)          => api.post(`${BASE}/${id}/annuler/`),

  // Public (no auth)
  submitPublic: (data) => publicClient.post('/public/demandes/', data),
};
