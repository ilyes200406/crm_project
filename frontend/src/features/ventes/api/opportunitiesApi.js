/**
 * OPPORTUNITIES API SERVICE
 */

import { api } from '../../../services/axios';

const BASE = '/ventes/opportunities';

export const opportunitiesApi = {
  getAll:          (params = {}) => api.get(`${BASE}/`, { params }),
  getById:         (id)          => api.get(`${BASE}/${id}/`),
  create:          (data)        => api.post(`${BASE}/`, data),
  update:          (id, data)    => api.patch(`${BASE}/${id}/`, data),
  delete:          (id)          => api.delete(`${BASE}/${id}/`),

  getStats:        ()            => api.get(`${BASE}/stats/`),
  getPipeline:     ()            => api.get(`${BASE}/pipeline/`),
  getRevenueChart: (months = 6)  => api.get(`${BASE}/revenue_chart/`, { params: { months } }),

  getRenewals:     (params = {}) => api.get(`${BASE}/renewals/`, { params }),
  getInitials:     (params = {}) => api.get(`${BASE}/initials/`, { params }),
  getUpsells:      (params = {}) => api.get(`${BASE}/upsells/`, { params }),

  requestSupplierQuotes: (id)        => api.post(`${BASE}/${id}/request_supplier_quotes/`),
  createInsomeaQuote:    (id, data)   => api.post(`${BASE}/${id}/create_insomea_quote/`, data),
  requestClientPO:       (id)        => api.post(`${BASE}/${id}/request_client_po/`),
  uploadClientPO:        (id, data)   => api.post(`${BASE}/${id}/upload_client_po/`, data, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }),
  approve:         (id)          => api.post(`${BASE}/${id}/approve/`),
  confirmAllPOs:   (id)          => api.post(`${BASE}/${id}/confirm_all_pos/`),
  cancel:          (id, reason)  => api.post(`${BASE}/${id}/cancel/`, { reason }),
  rollbackInsomeaQuote:   (id) => api.post(`${BASE}/${id}/rollback_insomea_quote/`),
  regenerateQuotePdf:     (id) => api.post(`${BASE}/${id}/regenerate_quote_pdf/`),
};
