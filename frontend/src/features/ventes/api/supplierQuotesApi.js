/**
 * SUPPLIER QUOTES API SERVICE
 */

import { api } from '../../../services/axios';

const BASE = '/ventes/supplier-quotes';

export const supplierQuotesApi = {
  getAll:   (params = {}) => api.get(`${BASE}/`, { params }),
  getById:  (id)          => api.get(`${BASE}/${id}/`),

  /**
   * Create supplier quote (multipart/form-data)
   *
   * Body:
   *   supplier_id, reference, document (File),
   *   discount_percent, lines (JSON string or array)
   *
   * lines items: { line_id, unit_price_purchase, sku?, currency?, delivery_time? }
   */
  create: (data) =>
    api.post(`${BASE}/`, data, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),

  download: (id) => api.get(`${BASE}/${id}/download/`, { responseType: 'blob' }),
};
