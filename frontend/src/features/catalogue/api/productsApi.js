/**
 * PRODUCTS API SERVICE
 * 
 * Endpoints pour catalogue produits (READ-ONLY)
 */

import { api } from '../../../services/axios';

export const productsApi = {
  /**
   * Get all products
   * 
   * @param {Object} params - Query params
   * @param {string} params.search - Search query (sku, title)
   * @param {string} params.category - Filter by category
   * @param {string} params.supplier - Filter by supplier ID
   * @param {boolean} params.is_active - Filter active products
   * @param {boolean} params.is_deprecated - Filter deprecated products
   * @param {number} params.limit - Limit results
   * @param {number} params.offset - Offset for pagination
   * @returns {Promise}
   */
  getAll: (params = {}) => {
    return api.get('/products/', { params });
  },

  /**
   * Get product by ID
   * 
   * @param {string} id - Product UUID
   * @returns {Promise}
   */
  getById: (id) => {
    return api.get(`/products/${id}/`);
  },

  /**
   * Search products
   * 
   * @param {string} query - Search query
   * @returns {Promise}
   */
  search: (query) => {
    return api.get('/products/', { params: { search: query } });
  },
};