/**
 * OPPORTUNITY LINES API SERVICE
 * Lines are nested under /ventes/opportunities/{opportunityId}/lines/
 */

import { api } from '../../../services/axios';

const BASE = (opportunityId) => `/ventes/opportunities/${opportunityId}/lines`;

export const linesApi = {
  getAll:    (opportunityId, params = {}) => api.get(`${BASE(opportunityId)}/`, { params }),
  getById:   (opportunityId, id)          => api.get(`${BASE(opportunityId)}/${id}/`),
  create:    (opportunityId, data)        => api.post(`${BASE(opportunityId)}/`, data),
  update:    (opportunityId, id, data)    => api.patch(`${BASE(opportunityId)}/${id}/`, data),
  delete:    (opportunityId, id)          => api.delete(`${BASE(opportunityId)}/${id}/`),
  cancel:    (opportunityId, id, reason)  => api.post(`${BASE(opportunityId)}/${id}/cancel/`, { reason }),
  confirmPO: (opportunityId, id)          => api.post(`${BASE(opportunityId)}/${id}/confirm-po/`),
  requestSupplierQuote: (opportunityId, id) =>
    api.post(`${BASE(opportunityId)}/${id}/request-supplier-quote/`),
};
