/**
 * NOTIFICATIONS API SERVICE
 * 
 * REST API endpoints pour notifications
 */

import { api } from '../../../services/axios';

export const notificationsApi = {
  /**
   * Get all notifications
   * 
   * @param {Object} params - Query params
   * @param {boolean} params.unread_only - Filter unread only
   * @param {number} params.limit - Limit results
   * @param {number} params.offset - Offset for pagination
   * @returns {Promise}
   */
  getAll: (params = {}) => {
    return api.get('/notifications/', { params });
  },

  /**
   * Get notification by ID
   * 
   * @param {string} id - Notification UUID
   * @returns {Promise}
   */
  getById: (id) => {
    return api.get(`/notifications/${id}/`);
  },

  /**
   * Mark notification as read
   * 
   * @param {string} id - Notification UUID
   * @returns {Promise}
   */
  markAsRead: (id) => {
    return api.post(`/notifications/${id}/mark_as_read/`);
  },

  /**
   * Mark all notifications as read
   * 
   * @returns {Promise}
   */
  markAllAsRead: () => {
    return api.post('/notifications/mark_all_as_read/');
  },

  /**
   * Delete notification
   * 
   * @param {string} id - Notification UUID
   * @returns {Promise}
   */
  delete: (id) => {
    return api.delete(`/notifications/${id}/`);
  },

  /**
   * Get unread count
   * 
   * @returns {Promise}
   */
  getUnreadCount: () => {
    return api.get('/notifications/unread_count/');
  },
};