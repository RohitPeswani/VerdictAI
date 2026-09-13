/**
 * VerdictAI API Client
 * Axios instance connecting to FastAPI backend (Darshan Prajapati - backend/app/api/v1/)
 * Base URL: http://localhost:8000/api/v1 (local dev) 
 */

import axios from 'axios';

// Backend base URL — change this to staging/production URL when deployed
const BASE_URL = 'http://localhost:8000/api/v1';

const apiClient = axios.create({
  baseURL: BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
    Accept: 'application/json',
  },
});

// ─── Request Interceptor (attach auth token when available) ───────────────
apiClient.interceptors.request.use(
  (config) => {
    // TODO Phase 4: attach JWT token from SecureStore
    // const token = await SecureStore.getItemAsync('auth_token');
    // if (token) config.headers.Authorization = `Bearer ${token}`;
    return config;
  },
  (error) => Promise.reject(error)
);

// ─── Response Interceptor (global error handling) ─────────────────────────
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response) {
      const message =
        error.response.data?.detail ||
        error.response.data?.message ||
        `HTTP ${error.response.status}: Request failed`;
      return Promise.reject(new Error(message));
    } else if (error.request) {
      return Promise.reject(
        new Error('Network error: Unable to reach VerdictAI server. Is the backend running?')
      );
    }
    return Promise.reject(error);
  }
);

export default apiClient;
