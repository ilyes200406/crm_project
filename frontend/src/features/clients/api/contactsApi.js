/**
 * CONTACTS API SERVICE
 * 
 * Endpoints pour contacts clients
 */

import { api } from '../../../services/axios';

export const contactsApi = {
  /**
   * Get all contacts for a client
   * 
   * @param {string} clientId - Client UUID
   * @param {Object} params - Query params
   * @returns {Promise}
   */
  getByClient: (clientId, params = {}) => {
    return api.get(`/clients/${clientId}/contacts/`, { params });
  },

  /**
   * Get contact by ID
   * 
   * @param {string} id - Contact UUID
   * @returns {Promise}
   */
  getById: (id) => {
    return api.get(`/clients/contacts/${id}/`);
  },

  /**
   * Create contact
   * 
   * @param {string} clientId - Client UUID
   * @param {Object} data - Contact data
   * @param {string} data.first_name - First name (required)
   * @param {string} data.last_name - Last name (required)
   * @param {string} data.email - Email (required)
   * @param {string} data.position - Job position
   * @param {string} data.phone - Phone number
   * @param {boolean} data.is_primary - Is primary contact
   * @param {string} data.notes - Notes
   * @returns {Promise}
   */
  create: (clientId, data) => {
    return api.post('/clients/contacts/', {
      ...data,
      client: clientId,
    });
  },

  /**
   * Update contact
   * 
   * @param {string} id - Contact UUID
   * @param {Object} data - Update data
   * @returns {Promise}
   */
  update: (id, data) => {
    return api.patch(`/clients/contacts/${id}/`, data);
  },

  /**
   * Delete contact
   * 
   * @param {string} id - Contact UUID
   * @returns {Promise}
   */
  delete: (id) => {
    return api.delete(`/clients/contacts/${id}/`);
  },
};