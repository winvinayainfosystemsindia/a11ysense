import React from 'react';
import { Box, Card, Typography, Grid, IconButton, CircularProgress, Stack } from '@mui/material';
import SearchIcon from '@mui/icons-material/Search';
import WarningIcon from '@mui/icons-material/Warning';
import DescriptionIcon from '@mui/icons-material/Description';
import LayersIcon from '@mui/icons-material/Layers';
import MoreVertIcon from '@mui/icons-material/MoreVert';
import StorageIcon from '@mui/icons-material/Storage';
import SpeedIcon from '@mui/icons-material/Speed';
import { StatCard } from '../common/stats';
import type { DashboardStats as StatsType } from '../../model/dashboard.model';
import { useAppSelector } from '../../store';
import type { PrometheusMetric } from '../../model/metrics.model';

interface DashboardStatsProps {
  stats: StatsType | null;
}

export const DashboardStats: React.FC<DashboardStatsProps> = ({ stats }) => {
  const { metrics } = useAppSelector((state) => state.metrics);

  const score = Math.round(stats?.average_score || 0);
  const totalScans = stats?.total_audits ?? 0;
  const critical = stats?.violations_by_impact?.critical || 0;
  const totalViolations = stats?.total_violations ?? 0;
  const activeAgents = stats?.active_audits_count ?? 0;

  // Compute System Diagnostics metrics
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
    if (i >= sizes.length) return bytes + ' B';
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <Grid container spacing={3}>
      {/* Left Side: Circular score gauge */}
      <Grid size={{ xs: 12, md: 4 }}>
        <Card variant="outlined" sx={{ p: 3.5, height: '100%', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', bgcolor: 'background.paper' }}>
          <Typography variant="subtitle2" sx={{ fontWeight: '800', color: 'text.secondary', mb: 3.5, alignSelf: 'flex-start', textTransform: 'uppercase', letterSpacing: '0.5px', fontSize: '0.72rem' }}>
            Global Accessibility Score
          </Typography>

          <Box sx={{ position: 'relative', display: 'inline-flex', mb: 3.5 }}>
            {/* Underlay Circle */}
            <CircularProgress
              variant="determinate"
              value={100}
              size={140}
              thickness={6.5}
              sx={{ color: 'divider' }}
            />
            {/* Overlay Circular Progress */}
            <CircularProgress
              variant="determinate"
              value={score}
              size={140}
              thickness={6.5}
              color="primary"
              sx={{
                position: 'absolute',
                left: 0,
                '& .MuiCircularProgress-svg': { strokeLinecap: 'round' }
              }}
            />
            {/* Inner Circle content */}
            <Box
              sx={{
                top: 0, left: 0, bottom: 0, right: 0,
                position: 'absolute', display: 'flex',
                alignItems: 'center', justifyContent: 'center',
                flexDirection: 'column'
              }}
            >
              <Typography variant="h3" component="div" sx={{ fontWeight: '800', color: 'text.primary', fontFamily: 'Outfit' }}>
                {score}
              </Typography>
            </Box>
          </Box>

          {/* Target & Benchmark Footer Row */}
          <Stack component="div" direction="row" spacing={2.5} sx={{ width: '100%', mt: 'auto' }}>
            <Box sx={{ flex: 1, p: 1.5, bgcolor: 'background.default', border: '1px solid', borderColor: 'divider', borderRadius: '12px', textAlign: 'center' }}>
              <Typography variant="caption" sx={{ color: 'text.disabled', fontWeight: '800', fontSize: '0.65rem', letterSpacing: '0.5px' }}>BENCHMARK</Typography>
              <Typography variant="body1" sx={{ fontWeight: '700', color: 'text.primary', mt: 0.25 }}>72.0</Typography>
            </Box>
            <Box sx={{ flex: 1, p: 1.5, bgcolor: 'background.default', border: '1px solid', borderColor: 'divider', borderRadius: '12px', textAlign: 'center' }}>
              <Typography variant="caption" sx={{ color: 'text.disabled', fontWeight: '800', fontSize: '0.65rem', letterSpacing: '0.5px' }}>TARGET</Typography>
              <Typography variant="body1" sx={{ fontWeight: '700', color: 'text.primary', mt: 0.25 }}>95.0</Typography>
            </Box>
          </Stack>
        </Card>
      </Grid>

      {/* Right Side: Cards grid (Row 1: 4 cards, Row 2: 3 cards) */}
      <Grid size={{ xs: 12, md: 8 }}>
        <Grid container spacing={3} sx={{ height: '100%', alignContent: 'stretch' }}>
          
          {/* ──── ROW 1: General Accessibility Stats (4 Cards) ──── */}
          
          {/* Total Scans */}
          <Grid size={{ xs: 12, sm: 6, md: 3 }} sx={{ display: 'flex', flexDirection: 'column' }}>
            <StatCard
              title="Total Scans"
              value={totalScans}
              icon={<SearchIcon />}
              color="primary.main"
            />
          </Grid>

          {/* Total Violations */}
          <Grid size={{ xs: 12, sm: 6, md: 3 }} sx={{ display: 'flex', flexDirection: 'column' }}>
            <StatCard
              title="Total Violations"
              value={totalViolations}
              icon={<DescriptionIcon />}
              color="secondary.main"
            />
          </Grid>

          {/* Critical Issues */}
          <Grid size={{ xs: 12, sm: 6, md: 3 }} sx={{ display: 'flex', flexDirection: 'column' }}>
            <StatCard
              title="Critical Issues"
              value={critical}
              icon={<WarningIcon />}
              color="error.main"
            />
          </Grid>

          {/* Active Agents */}
          <Grid size={{ xs: 12, sm: 6, md: 3 }} sx={{ display: 'flex', flexDirection: 'column' }}>
            <StatCard
              title="Active Agents"
              value={activeAgents}
              icon={<LayersIcon />}
              color="success.main"
              sx={{ position: 'relative' }}
            >
              <IconButton
                size="small"
                sx={{ position: 'absolute', top: 20, right: 20, color: 'text.disabled' }}
              >
                <MoreVertIcon fontSize="small" />
              </IconButton>
            </StatCard>
          </Grid>

          {/* ──── ROW 2: System Diagnostics (3 Cards) ──── */}

          {/* Response Payload Size */}
          <Grid size={{ xs: 12, sm: 4, md: 4 }} sx={{ display: 'flex', flexDirection: 'column' }}>
            <StatCard
              title="Response Payload Size"
              value={formatBytes(responseBytesTotal)}
              icon={<StorageIcon />}
              color="primary.main"
            />
          </Grid>

          {/* Request Payload Size */}
          <Grid size={{ xs: 12, sm: 4, md: 4 }} sx={{ display: 'flex', flexDirection: 'column' }}>
            <StatCard
              title="Request Payload Size"
              value={formatBytes(requestBytesTotal)}
              icon={<StorageIcon />}
              color="success.main"
            />
          </Grid>

          {/* Total API Requests */}
          <Grid size={{ xs: 12, sm: 4, md: 4 }} sx={{ display: 'flex', flexDirection: 'column' }}>
            <StatCard
              title="Total API Requests"
              value={requestsTotal.toLocaleString()}
              icon={<SpeedIcon />}
              color="secondary.main"
            />
          </Grid>

        </Grid>
      </Grid>
    </Grid>
  );
};
