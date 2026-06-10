import React, { useEffect } from 'react';
import {
  Card,
  CardContent,
  CardHeader,
  Typography,
  Grid,
  Box,
  CircularProgress,
  IconButton,
  Tooltip,
} from '@mui/material';
import RefreshIcon from '@mui/icons-material/Refresh';

import StorageIcon from '@mui/icons-material/Storage';
import SpeedIcon from '@mui/icons-material/Speed';

import { useAppDispatch, useAppSelector } from '../../store';
import { fetchSystemMetrics } from '../../store/slices/metricsSlice';
import type { PrometheusMetric } from '../../model/metrics.model';

export const SystemMetricsPanel: React.FC = () => {
  const dispatch = useAppDispatch();
  // We use useAppSelector and pick metrics slice
  const { metrics, loading, lastUpdated } = useAppSelector((state) => state.metrics);

  const loadData = () => {
    dispatch(fetchSystemMetrics());
  };

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 30000); // refresh every 30s
    return () => clearInterval(interval);
  }, [dispatch]);


  const responseBytesTotal = metrics
    .filter((m: PrometheusMetric) => m.name === 'http_response_size_bytes_sum')
    .reduce((sum: number, m: PrometheusMetric) => sum + m.value, 0);

  const requestBytesTotal = metrics
    .filter((m: PrometheusMetric) => m.name === 'http_request_size_bytes_sum')
    .reduce((sum: number, m: PrometheusMetric) => sum + m.value, 0);
  
  const requestsTotal = metrics
    .filter((m: PrometheusMetric) => m.name === 'http_requests_total')
    .reduce((sum: number, m: PrometheusMetric) => sum + m.value, 0);

  const formatBytes = (bytes: number) => {
    if (bytes === 0 || isNaN(bytes)) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    if (i >= sizes.length) return bytes + ' B'; // fallback
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <Card 
      sx={{ 
        height: '100%', 
        borderRadius: 4, 
        boxShadow: '0 8px 32px rgba(0,0,0,0.06)',
        border: '1px solid rgba(0,0,0,0.04)',
        background: 'linear-gradient(to right bottom, #ffffff, #fafafa)',
        overflow: 'hidden'
      }}
    >
      <CardHeader
        title="System Diagnostics"
        titleTypographyProps={{ variant: 'h6', fontWeight: 800, color: 'text.primary' }}
        sx={{ borderBottom: '1px solid rgba(0,0,0,0.04)', pb: 2, pt: 3, px: 4 }}
        action={
          <Tooltip title="Refresh metrics">
            <IconButton onClick={loadData} disabled={loading}>
              <RefreshIcon />
            </IconButton>
          </Tooltip>
        }
      />
      <CardContent sx={{ px: 4, py: 4 }}>
        {loading && !metrics.length ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 120 }}>
            <CircularProgress size={36} thickness={4} />
          </Box>
        ) : (
          <Grid container spacing={3}>
            <Grid size={{ xs: 12, sm: 4 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                <Box sx={{ p: 2, borderRadius: 3, background: 'linear-gradient(135deg, rgba(25, 118, 210, 0.15) 0%, rgba(25, 118, 210, 0.05) 100%)', color: '#1976d2', boxShadow: 'inset 0 0 0 1px rgba(25, 118, 210, 0.1)' }}>
                  <StorageIcon fontSize="large" />
                </Box>
                <Box>
                  <Typography variant="body2" color="text.secondary" sx={{ fontWeight: 600, letterSpacing: '0.5px', textTransform: 'uppercase', fontSize: '0.75rem', mb: 0.5 }}>
                    Response Payload Size
                  </Typography>
                  <Typography variant="h4" sx={{ fontWeight: 800, color: 'text.primary', letterSpacing: '-0.5px' }}>
                    {formatBytes(responseBytesTotal)}
                  </Typography>
                </Box>
              </Box>
            </Grid>
            <Grid size={{ xs: 12, sm: 4 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                <Box sx={{ p: 2, borderRadius: 3, background: 'linear-gradient(135deg, rgba(46, 125, 50, 0.15) 0%, rgba(46, 125, 50, 0.05) 100%)', color: '#2e7d32', boxShadow: 'inset 0 0 0 1px rgba(46, 125, 50, 0.1)' }}>
                  <StorageIcon fontSize="large" />
                </Box>
                <Box>
                  <Typography variant="body2" color="text.secondary" sx={{ fontWeight: 600, letterSpacing: '0.5px', textTransform: 'uppercase', fontSize: '0.75rem', mb: 0.5 }}>
                    Request Payload Size
                  </Typography>
                  <Typography variant="h4" sx={{ fontWeight: 800, color: 'text.primary', letterSpacing: '-0.5px' }}>
                    {formatBytes(requestBytesTotal)}
                  </Typography>
                </Box>
              </Box>
            </Grid>
            <Grid size={{ xs: 12, sm: 4 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                <Box sx={{ p: 2, borderRadius: 3, background: 'linear-gradient(135deg, rgba(156, 39, 176, 0.15) 0%, rgba(156, 39, 176, 0.05) 100%)', color: '#9c27b0', boxShadow: 'inset 0 0 0 1px rgba(156, 39, 176, 0.1)' }}>
                  <SpeedIcon fontSize="large" />
                </Box>
                <Box>
                  <Typography variant="body2" color="text.secondary" sx={{ fontWeight: 600, letterSpacing: '0.5px', textTransform: 'uppercase', fontSize: '0.75rem', mb: 0.5 }}>
                    Total API Requests
                  </Typography>
                  <Typography variant="h4" sx={{ fontWeight: 800, color: 'text.primary', letterSpacing: '-0.5px' }}>
                    {requestsTotal.toLocaleString()}
                  </Typography>
                </Box>
              </Box>
            </Grid>
          </Grid>
        )}
        {lastUpdated && (
          <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 3, textAlign: 'right' }}>
            Last updated: {new Date(lastUpdated).toLocaleTimeString()}
          </Typography>
        )}
      </CardContent>
    </Card>
  );
};
