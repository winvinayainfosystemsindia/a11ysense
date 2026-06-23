import { configureStore } from '@reduxjs/toolkit';
import type { Middleware } from '@reduxjs/toolkit';
import { useDispatch, useSelector } from 'react-redux';
import type { TypedUseSelectorHook } from 'react-redux';
import authReducer from './slices/authSlice';
import projectReducer from './slices/projectSlice';
import billingReducer from './slices/billingSlice';
import dashboardReducer from './slices/dashboardSlice';
import auditReducer from './slices/auditSlice';
import crawlDiscoveryReducer from './slices/crawlDiscoverySlice';
import adminReducer from './slices/adminSlice';
import metricsReducer from './slices/metricsSlice';

const toastMiddleware: Middleware = () => (next) => (action: any) => {
  if (action && action.type) {
    if (action.type.endsWith('/rejected')) {
      let errorMsg = action.payload || action.error?.message || 'An error occurred';
      let variant: 'error' | 'warning' | 'info' | 'success' = 'error';

      if (typeof action.payload === 'string' && action.payload.startsWith('[')) {
        const closingBracketIndex = action.payload.indexOf(']');
        if (closingBracketIndex > 0) {
          const metadata = action.payload.substring(1, closingBracketIndex);
          const [statusStr, severityStr] = metadata.split(':');
          const status = statusStr ? parseInt(statusStr, 10) : undefined;
          const severity = severityStr || undefined;

          errorMsg = action.payload.substring(closingBracketIndex + 1).trim();
          
          // Mutate payload to clean up metadata for slice extraReducers and unwraps
          action.payload = errorMsg;

          if (severity === 'success') {
            variant = 'success';
          } else if (severity === 'warning') {
            variant = 'warning';
          } else if (severity === 'info') {
            variant = 'info';
          } else if (severity === 'error') {
            variant = 'error';
          } else if (status) {
            if (status >= 400 && status < 500) {
              variant = 'warning';
            } else if (status >= 500) {
              variant = 'error';
            }
          }
        }
      }

      // Dispatch a custom event to show the toast globally
      const event = new CustomEvent('app-toast', {
        detail: { message: errorMsg, variant }
      });
      window.dispatchEvent(event);
    } else if (action.type.endsWith('/fulfilled')) {
      let successMsg = '';
      if (action.type === 'auth/login/fulfilled') {
        successMsg = 'Logged in successfully!';
      } else if (action.type === 'auth/register/fulfilled') {
        successMsg = 'Registration successful!';
      }
      
      if (successMsg) {
        const event = new CustomEvent('app-toast', {
          detail: { message: successMsg, variant: 'success' }
        });
        window.dispatchEvent(event);
      }
    } else if (action.type === 'auth/logoutUser') {
       const event = new CustomEvent('app-toast', {
        detail: { message: 'Signed out successfully', variant: 'info' }
      });
      window.dispatchEvent(event);
    }
  }
  return next(action);
};

export const store = configureStore({
  reducer: {
    auth: authReducer,
    project: projectReducer,
    billing: billingReducer,
    dashboard: dashboardReducer,
    audit: auditReducer,
    crawlDiscovery: crawlDiscoveryReducer,
    admin: adminReducer,
    metrics: metricsReducer,
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware().concat(toastMiddleware),
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;

export const useAppDispatch: () => AppDispatch = useDispatch;
export const useAppSelector: TypedUseSelectorHook<RootState> = useSelector;
