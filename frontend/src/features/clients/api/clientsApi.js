/**
 * CLIENTS API SERVICE
 * 
 * Endpoints pour clients (adapté au backend Django)
 */

import { api } from '../../../services/axios';

export const clientsApi = {
  /**
   * Get all clients
   * 
   * @param {Object} params - Query params
   * @param {string} params.search - Search query
   * @param {string} params.industry - Filter by industry
   * @param {boolean} params.is_active - Filter active/inactive
   * @param {number} params.limit - Limit results
   * @param {number} params.offset - Offset for pagination
   * @returns {Promise}
   */
  getAll: (params = {}) => {
    return api.get('/clients/', { params });
  },

  /**
   * Get client by ID
   * 
   * @param {string} id - Client UUID
   * @returns {Promise}
   */
  getById: (id) => {
    return api.get(`/clients/${id}/`);
  },

  /**
   * Create client
   * 
   * @param {Object} data - Client data
   * @param {string} data.company_name - Company name (required)
   * @param {string} data.industry - Industry choice (required)
   * @param {string} data.email - Email (required, unique)
   * @param {string} data.phone - Phone number
   * @param {string} data.website - Website URL
   * @param {string} data.address - Full address
   * @param {string} data.tenant_microsoft - Microsoft tenant ID
   * @param {string} data.notes - Notes
   * @param {string} data.assigned_to - Assigned user UUID
   * @returns {Promise}
   */
  create: (data) => {
    return api.post('/clients/', data);
  },

  /**
   * Update client
   * 
   * @param {string} id - Client UUID
   * @param {Object} data - Update data
   * @returns {Promise}
   */
  update: (id, data) => {
    return api.patch(`/clients/${id}/`, data);
  },

  /**
   * Delete client (soft delete)
   * 
   * @param {string} id - Client UUID
   * @returns {Promise}
   */
  delete: (id) => {
    return api.delete(`/clients/${id}/`);
  },

  /**
   * Assign client to user
   * 
   * @param {string} id - Client UUID
   * @param {string} assignedToId - User UUID
   * @returns {Promise}
   */
  assign: (id, assignedToId) => {
    return api.post(`/clients/${id}/assign/`, {
      assigned_to: assignedToId,
    });
  },

  /**
   * Restore soft-deleted client
   * 
   * @param {string} id - Client UUID
   * @returns {Promise}
   */
  restore: (id) => {
    return api.post(`/clients/${id}/restore/`);
  },

  /**
   * Get client stats
   * 
   * @returns {Promise}
   */
  getStats: () => {
    return api.get('/clients/stats/');
  },

  /**
   * Export clients
   * 
   * @param {Object} params - Query params
   * @param {string} params.format - Export format (csv, excel)
   * @returns {Promise}
   */
  export: (params = {}) => {
    return api.get('/clients/export/', { params });
  },

  /**
   * Get client activities
   * 
   * @param {string} id - Client UUID
   * @param {Object} params - Query params
   * @returns {Promise}
   */
  getActivities: (id, params = {}) => {
    return api.get(`/clients/${id}/activities/`, { params });
  },

  /**
   * Get client contacts
   * 
   * @param {string} id - Client UUID
   * @param {Object} params - Query params
   * @returns {Promise}
   */
  getContacts: (id, params = {}) => {
    return api.get(`/clients/${id}/contacts/`, { params });
  },
};