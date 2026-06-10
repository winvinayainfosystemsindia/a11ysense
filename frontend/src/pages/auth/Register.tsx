import React, { useState, useEffect } from 'react';
import { Grid, Typography, Box, Link as MuiLink } from '@mui/material';
import { useNavigate, Link } from '@tanstack/react-router';

import { useAppDispatch } from '../../store';
import { registerUser } from '../../store/slices/authSlice';
import { ShowcasePanel, RegisterForm } from '../../components/register';
import useToast from '../../hooks/useToast';

const Register: React.FC = () => {
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [orgName, setOrgName] = useState('');
  const [role, setRole] = useState('Viewer');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [agree, setAgree] = useState(true);
  
  const navigate = useNavigate();
  const dispatch = useAppDispatch();
  const toast = useToast();

  useEffect(() => {
    const token = localStorage.getItem('auth_token');
    const orgId = localStorage.getItem('org_id') || 'default';
    if (token) {
      navigate({ to: '/org/$orgId/dashboard', params: { orgId } });
    }
  }, [navigate]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!agree) {
      toast.warning('You must agree to the Terms of Service and Privacy Policy.');
      return;
    }
    setLoading(true);
    setSuccess(false);

    try {
      await dispatch(registerUser({
        email,
        password,
        organization_name: orgName || undefined,
        role
      })).unwrap();
      setSuccess(true);
      // Wait a moment and navigate to login
      setTimeout(() => {
        navigate({ to: '/auth/signin' });
      }, 1500);
    } catch (err: any) {
      // Error is caught globally by toastMiddleware
    } finally {
      setLoading(false);
    }
  };

  return (
    <Grid container sx={{ height: '100vh', overflow: 'hidden' }}>
      {/* Left Column - Brand & Showcase */}
      <Grid size={{ xs: 12, md: 5 }} sx={{
        height: '100vh',
        overflow: 'hidden',
        background: (theme) => `linear-gradient(135deg, ${theme.palette.text.primary} 0%, #020617 100%)`,
        color: 'common.white',
        borderRight: '1px solid rgba(255, 255, 255, 0.08)'
      }}>
        <ShowcasePanel />
      </Grid>

      {/* Right Column - Register Form */}
      <Grid size={{ xs: 12, md: 7 }} sx={{
        height: '100vh',
        overflow: 'hidden',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        backgroundColor: 'background.default',
        p: { xs: 3, sm: 4, md: 5 },
        position: 'relative'
      }}>
        <Box sx={{ width: '100%', maxWidth: 460 }}>
          {/* Modular Register Form */}
          <RegisterForm
            fullName={fullName}
            setFullName={setFullName}
            email={email}
            setEmail={setEmail}
            orgName={orgName}
            setOrgName={setOrgName}
            role={role}
            setRole={setRole}
            password={password}
            setPassword={setPassword}
            showPassword={showPassword}
            setShowPassword={setShowPassword}
            agree={agree}
            setAgree={setAgree}
            loading={loading}
            success={success}
            onSubmit={handleSubmit}
          />

          {/* Footer Navigation */}
          <Box sx={{ mt: 2, textAlign: 'center' }}>
            <Typography variant="body2" sx={{ color: 'text.secondary', fontWeight: '500', fontSize: '0.8rem' }}>
              Already have an account?{' '}
              <MuiLink component={Link} to="/auth/signin" sx={{ color: 'primary.main', fontWeight: '700', textDecoration: 'none', '&:hover': { textDecoration: 'underline' } }}>
                Sign In
              </MuiLink>
            </Typography>

            <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 1.5, fontWeight: 500, fontSize: '0.7rem' }}>
              &copy; {new Date().getFullYear()} A11ySense AI. All rights reserved.
            </Typography>
          </Box>
        </Box>
      </Grid>
    </Grid>
  );
};

export default Register;
