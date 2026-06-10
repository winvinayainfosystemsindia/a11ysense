import React from 'react';
import { Box, Card, Typography, Grid, IconButton, CircularProgress, Stack } from '@mui/material';
import SearchIcon from '@mui/icons-material/Search';
import WarningIcon from '@mui/icons-material/Warning';
import DescriptionIcon from '@mui/icons-material/Description';
import LayersIcon from '@mui/icons-material/Layers';
import MoreVertIcon from '@mui/icons-material/MoreVert';
import { StatCard } from '../common/stats';
import type { DashboardStats as StatsType } from '../../model/dashboard.model';

interface DashboardStatsProps {
  stats: StatsType | null;
}

export const DashboardStats: React.FC<DashboardStatsProps> = ({ stats }) => {

  const score = Math.round(stats?.average_score || 0);
  const totalScans = stats?.total_audits ?? 0;
  const critical = stats?.violations_by_impact?.critical || 0;
  const totalViolations = stats?.total_violations ?? 0;
  const activeAgents = stats?.active_audits_count ?? 0;

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

      {/* Right Side: 2x2 cards layout */}
      <Grid size={{ xs: 12, md: 8 }}>
        <Grid container spacing={3} sx={{ height: '100%' }}>
          {/* Total Scans Card */}
          <Grid size={{ xs: 12, sm: 6 }} sx={{ display: 'flex', flexDirection: 'column' }}>
            <StatCard
              title="Total Scans"
              value={totalScans}
              icon={<SearchIcon />}
              color="primary.main"
            />
          </Grid>

          {/* Critical Issues Card */}
          <Grid size={{ xs: 12, sm: 6 }} sx={{ display: 'flex', flexDirection: 'column' }}>
            <StatCard
              title="Critical Issues"
              value={critical}
              icon={<WarningIcon />}
              color="error.main"
            />
          </Grid>

          {/* Total Violations Card */}
          <Grid size={{ xs: 12, sm: 6 }} sx={{ display: 'flex', flexDirection: 'column' }}>
            <StatCard
              title="Total Violations"
              value={totalViolations}
              icon={<DescriptionIcon />}
              color="secondary.main"
            />
          </Grid>

          {/* Active Agents Card */}
          <Grid size={{ xs: 12, sm: 6 }} sx={{ display: 'flex', flexDirection: 'column' }}>
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
        </Grid>
      </Grid>
    </Grid>
  );
};
