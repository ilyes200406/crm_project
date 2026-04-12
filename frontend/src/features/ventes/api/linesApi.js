/**
 * OPPORTUNITY LINES API SERVICE
 */

import { api } from '../../../services/axios';

const BASE = '/ventes/opportunity-lines';

export const linesApi = {
  getAll:   (params = {}) => api.get(`${BASE}/`, { params }),
  getById:  (id)          => api.get(`${BASE}/${id}/`),
  create:   (data)        => api.post(`${BASE}/`, data),
  update:   (id, data)    => api.patch(`${BASE}/${id}/`, data),
  delete:   (id)          => api.delete(`${BASE}/${id}/`),
  cancel:   (id, reason)  => api.post(`${BASE}/${id}/cancel/`, { reason }),
};
