/**
 * PROVISIONS API SERVICE
 */

import { api } from '../../../services/axios';

const BASE = '/ventes/provisions';

export const provisionsApi = {
  getAll:   (params = {}) => api.get(`${BASE}/`, { params }),
  getById:  (id)          => api.get(`${BASE}/${id}/`),
  start:    (id)          => api.post(`${BASE}/${id}/start/`),
  complete: (id, data)    => api.post(`${BASE}/${id}/complete/`, data),
  fail:     (id, msg)     => api.post(`${BASE}/${id}/fail/`, { error_message: msg }),
  retry:    (id)          => api.post(`${BASE}/${id}/retry/`),
};
