import { api } from '../../../services/axios';

export const authApi = {
  login: (payload) => api.post('/auth/login/', payload),
  setupAccount: (payload) => api.post('/auth/setup/', payload),
  forgotPassword: (payload) => api.post('/auth/forgot-password/', payload),
  resetPassword: (payload) => api.post('/auth/reset-password/', payload),
  changePassword: (payload) => api.put('/auth/change-password/', payload),
  logout: (refreshToken) => api.post('/auth/logout/', { refresh: refreshToken }),
  refresh: (refreshToken) => api.post('/auth/token/refresh/', refreshToken ? { refresh: refreshToken } : {}),
};
