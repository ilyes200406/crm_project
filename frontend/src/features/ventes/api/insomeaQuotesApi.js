/**
 * INSOMEA QUOTES API SERVICE
 */

import { api } from '../../../services/axios';

const BASE = '/ventes/insomea-quotes';

export const insomeaQuotesApi = {
  getAll:          (params = {})  => api.get(`${BASE}/`, { params }),
  getById:         (id)           => api.get(`${BASE}/${id}/`),
  getByOpportunity:(opportunityId)=> api.get(`${BASE}/by-opportunity/${opportunityId}/`),
  download:        (id)           => api.get(`${BASE}/${id}/download/`, { responseType: 'blob' }),
};
