import React, { useState, useEffect } from 'react';
import { Container, Box, Paper } from '@mui/material';
import { useNavigate } from '@tanstack/react-router';

import { useAppDispatch } from '../../store';
import { loginUser } from '../../store/slices/authSlice';
import { BrandHeader, LoginForm, LegalFooter } from '../../components/login';

const Login: React.FC = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);

  const navigate = useNavigate();
  const dispatch = useAppDispatch();

  useEffect(() => {
    // If already logged in, skip login
    const token = localStorage.getItem('auth_token');
    const orgId = localStorage.getItem('org_id') || 'default';
    if (token) {
      navigate({ to: '/org/$orgId/dashboard', params: { orgId } });
    }
  }, [navigate]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      const response = await dispatch(loginUser({ email, password })).unwrap();
      localStorage.setItem('org_id', response.organization_id);
      navigate({ to: '/org/$orgId/dashboard', params: { orgId: response.organization_id } });
    } catch (err: any) {
      // Error is caught globally by toastMiddleware
    } finally {
      setLoading(false);
    }
  };

  const handlePrefill = (role: 'admin' | 'auditor') => {
    setEmail(role === 'admin' ? 'admin@a11y.com' : 'auditor@a11y.com');
    setPassword('password');
  };

  return (
    <Box sx={{
      height: '100vh',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      backgroundColor: 'background.default',
      backgroundImage: (theme) => `radial-gradient(${theme.palette.divider} 1px, transparent 1px)`,
      backgroundSize: '20px 20px',
      position: 'relative',
      overflow: 'hidden',
      px: 2
    }}>
      <Container maxWidth="xs" sx={{ zIndex: 1, position: 'relative' }}>
        {/* Brand Header Component */}
        <BrandHeader />

        {/* Login Form Card */}
        <Paper elevation={0} sx={{
          p: { xs: 2.5, sm: 3 },
          borderRadius: '16px',
          borderColor: 'divider',
          backgroundColor: 'background.paper',
          boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.05), 0 4px 6px -4px rgba(0, 0, 0, 0.05)'
        }}>
          <Box sx={{ mb: 2 }}>
            <Typography variant="h6" sx={{ fontWeight: '700', color: 'text.primary', fontSize: '1.1rem' }}>
              Welcome Back
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ fontSize: '0.825rem' }}>
              Sign in to your account
            </Typography>
          </Box>

          <LoginForm
            email={email}
            setEmail={setEmail}
            password={password}
            setPassword={setPassword}
            showPassword={showPassword}
            setShowPassword={setShowPassword}
            loading={loading}
            onSubmit={handleSubmit}
            onPrefill={handlePrefill}
          />
        </Paper>

        {/* Legal Footer Component */}
        <LegalFooter />
      </Container>
    </Box>
  );
};

// Internal import helper inside parent if needed, otherwise import Typography directly from MUI
import { Typography } from '@mui/material';

export default Login;
