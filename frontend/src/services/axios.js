import axios from 'axios';

import { useAppStore } from '../app/store';

const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api';

export const api = axios.create({
  baseURL: BASE_URL,
  withCredentials: true,
  timeout: 15_000,
  headers: {
    'Content-Type': 'application/json',
  },
});

const refreshClient = axios.create({
  baseURL: BASE_URL,
  withCredentials: true,
  timeout: 15_000,
  headers: {
    'Content-Type': 'application/json',
  },
});

let refreshPromise = null;

async function refreshAccessToken() {
  const { refreshToken, setAccessToken, setRefreshToken, clearSession } = useAppStore.getState();

  try {
    const payload = refreshToken ? { refresh: refreshToken } : {};
    const { data } = await refreshClient.post('/auth/token/refresh/', payload);

    if (!data?.access) {
      throw new Error('Missing access token in refresh response.');
    }

    setAccessToken(data.access);
    if (data.refresh) {
      setRefreshToken(data.refresh);
    }

    return data.access;
  } catch (error) {
    clearSession();
    throw error;
  }
}

api.interceptors.request.use((config) => {
  const { accessToken } = useAppStore.getState();

  if (accessToken) {
    config.headers.Authorization = `Bearer ${accessToken}`;
  }

  return config;
});

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const status = error.response?.status;
    const originalRequest = error.config;

    if (!originalRequest || status !== 401 || originalRequest._retry) {
      return Promise.reject(error);
    }

    if (originalRequest.url?.includes('/auth/token/refresh/')) {
      useAppStore.getState().clearSession();
      return Promise.reject(error);
    }

    originalRequest._retry = true;

    if (!refreshPromise) {
      refreshPromise = refreshAccessToken().finally(() => {
        refreshPromise = null;
      });
    }

    try {
      const newAccessToken = await refreshPromise;
      originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;
      return api(originalRequest);
    } catch (refreshError) {
      return Promise.reject(refreshError);
    }
  }
);
