/**
 * SUBSCRIPTIONS API SERVICE
 */

import { api } from '../../../services/axios';

const BASE = '/ventes/subscriptions';

export const subscriptionsApi = {
  getAll:            (params = {})       => api.get(`${BASE}/`, { params }),
  getById:           (id)               => api.get(`${BASE}/${id}/`),
  update:            (id, data)         => api.patch(`${BASE}/${id}/`, data),

  getActive:         (params = {})       => api.get(`${BASE}/active/`, { params }),
  getExpiring:       (days = 30, params = {}) => api.get(`${BASE}/expiring/`, { params: { days, ...params } }),
  getPendingRenewal: (params = {})       => api.get(`${BASE}/pending_renewal/`, { params }),
  getStats:          ()                 => api.get(`${BASE}/stats/`),

  getRenewalData:    (id)               => api.get(`${BASE}/${id}/renewal_data/`),
  createRenewal:     (id, data = {})    => api.post(`${BASE}/${id}/create_renewal/`, data),
  cancel:            (id, reason)       => api.post(`${BASE}/${id}/cancel/`, { reason }),
};
