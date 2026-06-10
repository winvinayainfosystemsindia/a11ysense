import React, { useState, useEffect } from 'react';
import {
  Box,
  CircularProgress,
  Stack,
  Grid
} from '@mui/material';
import { useNavigate } from '@tanstack/react-router';

import { useAppDispatch, useAppSelector } from '../../store';
import { fetchDashboardStats } from '../../store/slices/dashboardSlice';
import { fetchSystemMetrics } from '../../store/slices/metricsSlice';
import {
  DashboardStats,
  CriticalIssuesChart,
  AgentActivityConsole,
  RecentAuditsTable,
  WelcomeHeader
} from '../../components/dashboard';
import { StartAuditDialog } from '../../components/audit/StartAuditDialog';

const Dashboard: React.FC = () => {
  const dispatch = useAppDispatch();
  const stats = useAppSelector((state) => state.dashboard.stats);
  const [loading, setLoading] = useState(true);
  const [timeRange, setTimeRange] = useState<'24h' | '7d' | '30d'>('24h');
  const [auditDialogOpen, setAuditDialogOpen] = useState(false);
  const navigate = useNavigate();

  // Read session profile details
  const orgName = localStorage.getItem('org_name') || 'Enterprise';

  const loadData = async (range: '24h' | '7d' | '30d' = timeRange) => {
    setLoading(true);
    try {
      await Promise.all([
        dispatch(fetchDashboardStats(range)).unwrap(),
        dispatch(fetchSystemMetrics()).unwrap()
      ]);
    } catch (err: any) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!localStorage.getItem('auth_token')) {
      navigate({ to: '/auth/signin' });
      return;
    }
    loadData(timeRange);
  }, [navigate, timeRange]);

  return (
    <Box sx={{ pb: 4 }}>
      <WelcomeHeader
        orgName={orgName}
        timeRange={timeRange}
        onTimeRangeChange={setTimeRange}
        onSync={() => loadData(timeRange)}
      />

      <Box sx={{ mt: 4 }}>
        {loading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '300px' }}>
            <CircularProgress size={50} color="primary" />
          </Box>
        ) : (
          <Stack component="div" spacing={4} sx={{ width: '100%' }}>
            <DashboardStats stats={stats} />

            <Grid container spacing={3}>
              <Grid size={{ xs: 12, md: 7 }}>
                <CriticalIssuesChart stats={stats} />
              </Grid>
              <Grid size={{ xs: 12, md: 5 }}>
                <AgentActivityConsole
                  stats={stats}
                  onNavigateToAudit={() => {
                    setAuditDialogOpen(true);
                  }}
                />
              </Grid>
            </Grid>

            <RecentAuditsTable stats={stats} onRefresh={loadData} />
          </Stack>
        )}
      </Box>
      <StartAuditDialog open={auditDialogOpen} onClose={() => setAuditDialogOpen(false)} />
    </Box>
  );
};

export default Dashboard;
