/**
 * SUPPLIERS API SERVICE
 * 
 * Endpoints pour fournisseurs (READ-ONLY pour tous)
 */

import { api } from '../../../services/axios';

export const suppliersApi = {
  /**
   * Get all suppliers
   * 
   * @param {Object} params - Query params
   * @param {string} params.search - Search query
   * @param {string} params.type - Filter by type (DIRECT, DISTRIBUTOR, RESELLER)
   * @param {boolean} params.is_active - Filter active suppliers
   * @returns {Promise}
   */
  getAll: (params = {}) => {
    return api.get('/suppliers/', { params });
  },

  /**
   * Get supplier by ID
   * 
   * @param {string} id - Supplier UUID
   * @returns {Promise}
   */
  getById: (id) => {
    return api.get(`/suppliers/${id}/`);
  },

  /**
   * Get supplier products
   * 
   * @param {string} id - Supplier UUID
   * @param {Object} params - Query params
   * @returns {Promise}
   */
  getProducts: (id, params = {}) => {
    return api.get(`/suppliers/${id}/products/`, { params });
  },

  /**
   * Get supplier stats
   * 
   * @returns {Promise}
   */
  getStats: () => {
    return api.get('/suppliers/stats/');
  },
};