import React, { useEffect } from 'react';
import { RouterProvider } from '@tanstack/react-router';
import { Provider as ReduxProvider } from 'react-redux';
import { ThemeProvider } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { SnackbarProvider } from 'notistack';
import { store } from './store';
import { theme } from './theme';
import { router } from './router';
import { AppProvider } from './context/AppContext';
import useToast from './hooks/useToast';

const ToastListener: React.FC = () => {
  const toast = useToast();

  useEffect(() => {
    const handleToast = (e: Event) => {
      const customEvent = e as CustomEvent<{ message: string; variant: 'success' | 'error' | 'info' | 'warning' }>;
      if (customEvent.detail && customEvent.detail.message) {
        toast.showToast(customEvent.detail.message, customEvent.detail.variant || 'default');
      }
    };

    window.addEventListener('app-toast', handleToast);
    return () => {
      window.removeEventListener('app-toast', handleToast);
    };
  }, [toast]);

  return null;
};

function App() {
  return (
    <ReduxProvider store={store}>
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <AppProvider>
          <SnackbarProvider maxSnack={3} autoHideDuration={3000}>
            <ToastListener />
            <RouterProvider router={router} />
          </SnackbarProvider>
        </AppProvider>
      </ThemeProvider>
    </ReduxProvider>
  );
}

export default App;
