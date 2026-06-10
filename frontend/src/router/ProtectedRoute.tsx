import React from 'react';
import { Navigate, Outlet } from '@tanstack/react-router';
import { MainLayout } from '../components/common/layout';

const ProtectedRoute: React.FC = () => {
  const token = localStorage.getItem('auth_token');

  if (!token) {
    return <Navigate to="/auth/signin" replace />;
  }

  return (
    <MainLayout>
      <Outlet />
    </MainLayout>
  );
};

export default ProtectedRoute;
