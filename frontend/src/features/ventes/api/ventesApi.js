/** 
import { api } from '../../../services/axios';

export const ventesApi = {
  // ── Opportunities ──────────────────────────────────────
  getOpportunityStats: () =>
    api.get('/ventes/opportunities/stats/'),

  getOpportunityPipeline: () =>
    api.get('/ventes/opportunities/pipeline/'),

  getOpportunities: (params) =>
    api.get('/ventes/opportunities/', { params }),

  getOpportunity: (id) =>
    api.get(`/ventes/opportunities/${id}/`),

  // ── Provisions ─────────────────────────────────────────
  getProvisions: (params) =>
    api.get('/ventes/provisions/', { params }),

  getProvision: (id) =>
    api.get(`/ventes/provisions/${id}/`),

  // ── Subscriptions ──────────────────────────────────────
  getSubscriptionStats: () =>
    api.get('/ventes/subscriptions/stats/'),

  getSubscriptions: (params) =>
    api.get('/ventes/subscriptions/', { params }),
};
*/