import React from 'react';
import { Grid } from '@mui/material';
import HubIcon from '@mui/icons-material/Hub';
import StorageIcon from '@mui/icons-material/Storage';
import WarningIcon from '@mui/icons-material/Warning';
import SpeedIcon from '@mui/icons-material/Speed';
import StatCard from '../common/stats/StatCard';
import type { TelemetryStats } from './types';

interface AgentsStatsGridProps {
  stats: TelemetryStats | null;
}

const AgentsStatsGrid: React.FC<AgentsStatsGridProps> = ({ stats }) => {
  return (
    <Grid container spacing={3}>
      <Grid size={{ xs: 12, sm: 6, md: 3 }}>
        <StatCard
          title="Active Agents"
          value={stats?.active_agents_count || 0}
          icon={<HubIcon />}
          color="primary.main"
          subtitle="Currently running execution loops"
        />
      </Grid>
      <Grid size={{ xs: 12, sm: 6, md: 3 }}>
        <StatCard
          title="Total Scans Executed"
          value={stats?.total_tasks_run || 0}
          icon={<StorageIcon />}
          color="secondary.main"
          subtitle={`${stats?.completed_tasks_run || 0} passed / ${stats?.failed_tasks_run || 0} failed`}
        />
      </Grid>
      <Grid size={{ xs: 12, sm: 6, md: 3 }}>
        <StatCard
          title="Compliance Violations"
          value={stats?.total_violations_found || 0}
          icon={<WarningIcon />}
          color="error.main"
          subtitle="Aggregated client accessibility defects"
        />
      </Grid>
      <Grid size={{ xs: 12, sm: 6, md: 3 }}>
        <StatCard
          title="LLM Token Usage"
          value={stats?.tokens?.total_tokens ? stats.tokens.total_tokens.toLocaleString() : '0'}
          icon={<SpeedIcon />}
          color="success.main"
          subtitle={`${(stats?.tokens?.input_tokens || 0).toLocaleString()} in / ${(stats?.tokens?.output_tokens || 0).toLocaleString()} out`}
        />
      </Grid>
    </Grid>
  );
};

export default AgentsStatsGrid;
