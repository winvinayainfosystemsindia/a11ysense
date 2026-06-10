import React from 'react';
import { Card, Typography, Grid, Box, Stack, alpha, useTheme } from '@mui/material';
import SmartToyIcon from '@mui/icons-material/SmartToy';
import HubIcon from '@mui/icons-material/Hub';
import StatusBadge from '../common/badge/StatusBadge';
import type { TelemetryStats } from './types';

interface AgentsTopologyProps {
  stats: TelemetryStats | null;
}

const AgentsTopology: React.FC<AgentsTopologyProps> = ({ stats }) => {
  const theme = useTheme();

  // Check which agents are currently active
  const isAgentActive = (agentType: 'manager' | 'spectre' | 'xray' | 'analyzer') => {
    if (!stats || stats.active_tasks.length === 0) return false;
    return stats.active_tasks.some((task) => {
      if (agentType === 'manager') return true;
      if (agentType === 'spectre') return task.status === 'crawling';
      if (agentType === 'xray') return task.status === 'auditing';
      if (agentType === 'analyzer') return task.status === 'processing';
      return false;
    });
  };

  const getActiveTaskForAgent = (agentType: 'spectre' | 'xray' | 'analyzer') => {
    if (!stats) return null;
    return stats.active_tasks.find((task) => {
      if (agentType === 'spectre') return task.status === 'crawling';
      if (agentType === 'xray') return task.status === 'auditing';
      if (agentType === 'analyzer') return task.status === 'processing';
      return false;
    }) || null;
  };

  const activeSpectreTask = getActiveTaskForAgent('spectre');
  const activeXrayTask = getActiveTaskForAgent('xray');
  const activeAnalyzerTask = getActiveTaskForAgent('analyzer');

  return (
    <Card variant="outlined" sx={{ p: 3, bgcolor: 'background.paper' }}>
      <Typography variant="h6" sx={{ fontWeight: '700', mb: 0.5 }}>
        Cluster Node Topology
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        Visual schema of autonomous processes cooperating in parallel tasks.
      </Typography>

      <Grid container spacing={3}>
        {/* Manager Agent */}
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <Box
            sx={{
              p: 2.5,
              border: '1px solid',
              borderColor: isAgentActive('manager') ? alpha(theme.palette.primary.main, 0.4) : 'divider',
              borderRadius: '12px',
              bgcolor: isAgentActive('manager') ? alpha(theme.palette.primary.main, 0.02) : 'transparent',
              display: 'flex',
              flexDirection: 'column',
              height: '100%',
              position: 'relative',
              transition: 'all 0.3s ease-in-out',
              '&:hover': {
                borderColor: 'primary.main',
                boxShadow: `0 4px 20px ${alpha(theme.palette.primary.main, 0.08)}`
              }
            }}
          >
            <Stack component="div" direction="row" spacing={1.5} sx={{ alignItems: 'center', mb: 2 }}>
              <Box sx={{ p: 1, borderRadius: '8px', bgcolor: alpha(theme.palette.primary.main, 0.1), color: 'primary.main', display: 'flex' }}>
                <HubIcon sx={{ fontSize: '1.25rem' }} />
              </Box>
              <Box>
                <Typography variant="subtitle2" sx={{ fontWeight: '700' }}>Manager Agent</Typography>
                <Typography variant="caption" color="text.disabled">Orchestrator</Typography>
              </Box>
            </Stack>
            <Typography variant="body2" color="text.secondary" sx={{ flexGrow: 1, mb: 2 }}>
              Listens to audit events, manages workflow state, and schedules crawl and analyze tasks.
            </Typography>
            <Box sx={{ mt: 'auto', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <StatusBadge
                label={isAgentActive('manager') ? 'Active' : 'Idle'}
                status={isAgentActive('manager') ? 'active' : 'inactive'}
              />
            </Box>
          </Box>
        </Grid>

        {/* Spectre Agent */}
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <Box
            sx={{
              p: 2.5,
              border: '1px solid',
              borderColor: activeSpectreTask ? alpha(theme.palette.info.main, 0.4) : 'divider',
              borderRadius: '12px',
              bgcolor: activeSpectreTask ? alpha(theme.palette.info.main, 0.02) : 'transparent',
              display: 'flex',
              flexDirection: 'column',
              height: '100%',
              transition: 'all 0.3s ease-in-out',
              '&:hover': {
                borderColor: 'info.main',
                boxShadow: `0 4px 20px ${alpha(theme.palette.info.main, 0.08)}`
              }
            }}
          >
            <Stack component="div" direction="row" spacing={1.5} sx={{ alignItems: 'center', mb: 2 }}>
              <Box sx={{ p: 1, borderRadius: '8px', bgcolor: alpha(theme.palette.info.main, 0.1), color: 'info.main', display: 'flex' }}>
                <SmartToyIcon sx={{ fontSize: '1.25rem' }} />
              </Box>
              <Box>
                <Typography variant="subtitle2" sx={{ fontWeight: '700' }}>Agent Spectre</Typography>
                <Typography variant="caption" color="text.disabled">Crawl Worker</Typography>
              </Box>
            </Stack>
            <Typography variant="body2" color="text.secondary" sx={{ flexGrow: 1, mb: 2 }}>
              Discovers sitemaps, traverses links, and compiles page lists to crawl downstream.
            </Typography>
            {activeSpectreTask && (
              <Box sx={{ p: 1.25, bgcolor: alpha(theme.palette.info.main, 0.04), borderRadius: '8px', border: `1px dashed ${alpha(theme.palette.info.main, 0.25)}`, mb: 2 }}>
                <Typography variant="caption" sx={{ display: 'block', fontWeight: '700', color: 'info.main', mb: 0.25, textTransform: 'uppercase', fontSize: '0.62rem' }}>CRAWLING URL</Typography>
                <Typography variant="body2" sx={{ fontWeight: '600', textOverflow: 'ellipsis', overflow: 'hidden', whiteSpace: 'nowrap' }}>
                  {activeSpectreTask.url}
                </Typography>
              </Box>
            )}
            <Box sx={{ mt: 'auto', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <StatusBadge
                label={activeSpectreTask ? 'Crawling' : 'Idle'}
                status={activeSpectreTask ? 'prospect' : 'inactive'}
              />
            </Box>
          </Box>
        </Grid>

        {/* X-Ray Agent */}
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <Box
            sx={{
              p: 2.5,
              border: '1px solid',
              borderColor: activeXrayTask ? alpha(theme.palette.warning.main, 0.4) : 'divider',
              borderRadius: '12px',
              bgcolor: activeXrayTask ? alpha(theme.palette.warning.main, 0.02) : 'transparent',
              display: 'flex',
              flexDirection: 'column',
              height: '100%',
              transition: 'all 0.3s ease-in-out',
              '&:hover': {
                borderColor: 'warning.main',
                boxShadow: `0 4px 20px ${alpha(theme.palette.warning.main, 0.08)}`
              }
            }}
          >
            <Stack component="div" direction="row" spacing={1.5} sx={{ alignItems: 'center', mb: 2 }}>
              <Box sx={{ p: 1, borderRadius: '8px', bgcolor: alpha(theme.palette.warning.main, 0.1), color: 'warning.main', display: 'flex' }}>
                <SmartToyIcon sx={{ fontSize: '1.25rem' }} />
              </Box>
              <Box>
                <Typography variant="subtitle2" sx={{ fontWeight: '700' }}>Agent X-Ray</Typography>
                <Typography variant="caption" color="text.disabled">MUI Compliance Scanner</Typography>
              </Box>
            </Stack>
            <Typography variant="body2" color="text.secondary" sx={{ flexGrow: 1, mb: 2 }}>
              Simulates browsers to run Axe-core tests and matches elements against a11y compliance rules.
            </Typography>
            {activeXrayTask && (
              <Box sx={{ p: 1.25, bgcolor: alpha(theme.palette.warning.main, 0.04), borderRadius: '8px', border: `1px dashed ${alpha(theme.palette.warning.main, 0.25)}`, mb: 2 }}>
                <Typography variant="caption" sx={{ display: 'block', fontWeight: '700', color: 'warning.main', mb: 0.25, textTransform: 'uppercase', fontSize: '0.62rem' }}>AUDITING PAGE</Typography>
                <Typography variant="body2" sx={{ fontWeight: '600', textOverflow: 'ellipsis', overflow: 'hidden', whiteSpace: 'nowrap' }}>
                  {activeXrayTask.url}
                </Typography>
                <Typography variant="caption" color="text.secondary" sx={{ fontWeight: '500', mt: 0.5, display: 'block' }}>
                  Scanned: {activeXrayTask.pages_completed}/{activeXrayTask.pages_total} pages
                </Typography>
              </Box>
            )}
            <Box sx={{ mt: 'auto', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <StatusBadge
                label={activeXrayTask ? 'Auditing' : 'Idle'}
                status={activeXrayTask ? 'nurturing' : 'inactive'}
              />
            </Box>
          </Box>
        </Grid>

        {/* Analyzer Agent */}
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <Box
            sx={{
              p: 2.5,
              border: '1px solid',
              borderColor: activeAnalyzerTask ? alpha(theme.palette.success.main, 0.4) : 'divider',
              borderRadius: '12px',
              bgcolor: activeAnalyzerTask ? alpha(theme.palette.success.main, 0.02) : 'transparent',
              display: 'flex',
              flexDirection: 'column',
              height: '100%',
              transition: 'all 0.3s ease-in-out',
              '&:hover': {
                borderColor: 'success.main',
                boxShadow: `0 4px 20px ${alpha(theme.palette.success.main, 0.08)}`
              }
            }}
          >
            <Stack component="div" direction="row" spacing={1.5} sx={{ alignItems: 'center', mb: 2 }}>
              <Box sx={{ p: 1, borderRadius: '8px', bgcolor: alpha(theme.palette.success.main, 0.1), color: 'success.main', display: 'flex' }}>
                <SmartToyIcon sx={{ fontSize: '1.25rem' }} />
              </Box>
              <Box>
                <Typography variant="subtitle2" sx={{ fontWeight: '700' }}>Agent Analyzer</Typography>
                <Typography variant="caption" color="text.disabled">Reports Engine</Typography>
              </Box>
            </Stack>
            <Typography variant="body2" color="text.secondary" sx={{ flexGrow: 1, mb: 2 }}>
              Consolidates structural accessibility report audits, calculates score trends, and exports findings.
            </Typography>
            {activeAnalyzerTask && (
              <Box sx={{ p: 1.25, bgcolor: alpha(theme.palette.success.main, 0.04), borderRadius: '8px', border: `1px dashed ${alpha(theme.palette.success.main, 0.25)}`, mb: 2 }}>
                <Typography variant="caption" sx={{ display: 'block', fontWeight: '700', color: 'success.main', mb: 0.25, textTransform: 'uppercase', fontSize: '0.62rem' }}>COMPILING REPORT</Typography>
                <Typography variant="body2" sx={{ fontWeight: '600', textOverflow: 'ellipsis', overflow: 'hidden', whiteSpace: 'nowrap' }}>
                  Task {activeAnalyzerTask.task_id.slice(0, 8)}...
                </Typography>
              </Box>
            )}
            <Box sx={{ mt: 'auto', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <StatusBadge
                label={activeAnalyzerTask ? 'Processing' : 'Idle'}
                status={activeAnalyzerTask ? 'converted' : 'inactive'}
              />
            </Box>
          </Box>
        </Grid>
      </Grid>
    </Card>
  );
};

export default AgentsTopology;
