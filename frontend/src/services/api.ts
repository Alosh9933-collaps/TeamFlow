import axios, { type InternalAxiosRequestConfig } from 'axios';

const configuredBaseUrl = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api/';
const API_BASE_URL = configuredBaseUrl.endsWith('/') ? configuredBaseUrl : `${configuredBaseUrl}/`;

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 15000,
  headers: { 'Content-Type': 'application/json' },
});

api.interceptors.request.use((config) => {
  const access = localStorage.getItem('access_token');
  if (access) config.headers.Authorization = `Bearer ${access}`;
  return config;
});

type RetryConfig = InternalAxiosRequestConfig & { _teamflowRetry?: boolean };

// Try refreshing an expired access token once, then retry the original request.
api.interceptors.response.use(
  (response) => response,
  async (error: unknown) => {
    if (!axios.isAxiosError(error) || !error.config || error.response?.status !== 401) {
      return Promise.reject(error);
    }

    const original = error.config as RetryConfig;
    const requestUrl = original.url || '';
    const refresh = localStorage.getItem('refresh_token');

    if (!refresh || original._teamflowRetry || requestUrl.includes('auth/token')) {
      return Promise.reject(error);
    }

    original._teamflowRetry = true;
    try {
      const response = await axios.post(`${API_BASE_URL}auth/token/refresh/`, { refresh });
      const newAccess = response.data.access as string;
      localStorage.setItem('access_token', newAccess);
      original.headers.Authorization = `Bearer ${newAccess}`;
      return api(original);
    } catch (refreshError) {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      window.dispatchEvent(new Event('teamflow:unauthorized'));
      return Promise.reject(refreshError);
    }
  },
);

export default api;
