import axios from 'axios';
import { ENV } from '../config/env';

const api = axios.create({
  baseURL: ENV.API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('auth_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

let isRefreshing = false;
let failedQueue: any[] = [];

const processQueue = (error: any, token: string | null = null) => {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(token);
    }
  });
  failedQueue = [];
};

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    const data = error.response?.data;
    const status = error.response?.status;

    if (status === 401 && originalRequest && !originalRequest._retry) {
      const isAuthPage = window.location.pathname.includes('/auth/');
      if (!isAuthPage) {
        const refreshToken = localStorage.getItem('refresh_token');
        if (!refreshToken) {
          import('../store').then(({ store }) => {
            import('../store/slices/authSlice').then(({ logoutUser }) => {
              store.dispatch(logoutUser());
              window.location.href = '/auth/signin';
            });
          });
          return Promise.reject(error);
        }

        originalRequest._retry = true;

        if (isRefreshing) {
          return new Promise((resolve, reject) => {
            failedQueue.push({ resolve, reject });
          })
            .then((token) => {
              originalRequest.headers.Authorization = `Bearer ${token}`;
              return api(originalRequest);
            })
            .catch((err) => {
              return Promise.reject(err);
            });
        }

        isRefreshing = true;

        try {
          const response = await axios.post(`${ENV.API_URL}/auth/refresh`, {
            refresh_token: refreshToken,
          });

          const { access_token, refresh_token } = response.data;

          localStorage.setItem('auth_token', access_token);
          localStorage.setItem('refresh_token', refresh_token);

          const { store } = await import('../store');
          const { refreshUserToken } = await import('../store/slices/authSlice');
          store.dispatch({
            type: refreshUserToken.fulfilled.type,
            payload: response.data
          });

          processQueue(null, access_token);

          originalRequest.headers.Authorization = `Bearer ${access_token}`;
          return api(originalRequest);
        } catch (refreshError) {
          processQueue(refreshError, null);
          
          const { store } = await import('../store');
          const { logoutUser } = await import('../store/slices/authSlice');
          store.dispatch(logoutUser());
          window.location.href = '/auth/signin';
          
          return Promise.reject(refreshError);
        } finally {
          isRefreshing = false;
        }
      }
    }

    let message = 'An unexpected error occurred. Please try again.';

    // Robust extraction function that parses arbitrary error response formats
    const extractedMessage = (() => {
      if (!data) return null;
      if (typeof data === 'string') return data;
      if (typeof data === 'object') {
        // Direct common error fields
        if (typeof data.message === 'string' && data.message.trim()) return data.message;
        if (typeof data.detail === 'string' && data.detail.trim()) return data.detail;
        if (typeof data.error === 'string' && data.error.trim()) return data.error;
        if (typeof data.msg === 'string' && data.msg.trim()) return data.msg;

        // FastAPI-style validation array inside 'detail'
        if (Array.isArray(data.detail)) {
          try {
            return data.detail
              .map((err: any) => {
                if (typeof err === 'string') return err;
                if (err && typeof err === 'object') {
                  const loc = err.loc ? err.loc.filter((l: any) => l !== 'body' && l !== 'query').join('.') : '';
                  const msg = err.msg || err.message || JSON.stringify(err);
                  return loc ? `${loc}: ${msg}` : msg;
                }
                return String(err);
              })
              .filter(Boolean)
              .join(' | ');
          } catch {
            // ignore fallback
          }
        }

        // Generic arrays of error objects
        if (Array.isArray(data.errors)) {
          try {
            return data.errors
              .map((err: any) => {
                if (typeof err === 'string') return err;
                if (err && typeof err === 'object') {
                  return err.message || err.msg || err.detail || JSON.stringify(err);
                }
                return String(err);
              })
              .filter(Boolean)
              .join(' | ');
          } catch {
            // ignore fallback
          }
        }

        // Nested error object
        if (data.error && typeof data.error === 'object') {
          const nestedMsg = data.error.message || data.error.detail || data.error.msg;
          if (typeof nestedMsg === 'string' && nestedMsg.trim()) return nestedMsg;
        }

        // Search for any string property as a fallback
        const stringValues = Object.values(data).filter((v) => typeof v === 'string') as string[];
        if (stringValues.length > 0) {
          const suitableVal = stringValues.find((s) => s.length > 10) || stringValues[0];
          if (suitableVal && suitableVal.trim()) return suitableVal;
        }
      }
      return null;
    })();

    if (extractedMessage) {
      message = extractedMessage;
    } else if (error.request) {
      message = 'Unable to reach the server. Check your network connection.';
    }

    if (!extractedMessage) {
      const statusMessages: Record<number, string> = {
        400: 'Invalid request. Please check your input.',
        401: 'Unauthorised. Please sign in again.',
        403: 'You do not have permission to perform this action.',
        404: 'The requested resource was not found.',
        409: 'A conflict occurred. The resource may already exist.',
        422: 'Validation error. Please check the submitted data.',
        429: 'Too many requests. Please slow down.',
        500: 'An internal server error occurred. Please try again later.',
        502: 'Server gateway error. Please try again.',
        503: 'Service temporarily unavailable. Please try again.',
      };
      message = statusMessages[status] || message;
    }

    const severity = data?.severity || (status && status >= 500 ? 'error' : 'warning') || 'error';
    (error as any).userMessage = `[${status || ''}:${severity}] ${message}`;
    return Promise.reject(error);
  }
);

export default api;


