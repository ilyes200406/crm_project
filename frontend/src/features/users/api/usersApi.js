import { api } from '../../../services/axios';

export const usersApi = {
  me: () => api.get('/auth/me/'),
  updateMe: (payload) => api.patch('/auth/me/', payload),
  createUser: (payload) => api.post('/auth/admin/create-user/', payload),
  listUsers: (params) => api.get('/auth/users/', { params }),
  getUser: (id) => api.get(`/auth/users/${id}/`),
  updateUser: (id, payload) => api.patch(`/auth/users/${id}/`, payload),
  deactivateUser: (id) => api.delete(`/auth/users/${id}/`),
  activateUser: (id) => api.post(`/auth/users/${id}/activate/`),
  userStats: () => api.get('/auth/users/stats/'),
};
