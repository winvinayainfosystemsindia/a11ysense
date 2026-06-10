import React from 'react';
import { Card, Stack, Box, Typography } from '@mui/material';
import type { DashboardStats as StatsType } from '../../model/dashboard.model';

interface CriticalIssuesChartProps {
  stats: StatsType | null;
}

export const CriticalIssuesChart: React.FC<CriticalIssuesChartProps> = ({ stats }) => {
  const critical = stats?.violations_by_impact?.critical || 0;
  const serious = stats?.violations_by_impact?.serious || 0;
  const moderate = stats?.violations_by_impact?.moderate || 0;
  const minor = stats?.violations_by_impact?.minor || 0;

  const maxViolations = Math.max(critical, serious, moderate, minor, 1);
  const criticalHeight = `${(critical / maxViolations) * 100}%`;
  const seriousHeight = `${(serious / maxViolations) * 100}%`;
  const moderateHeight = `${(moderate / maxViolations) * 100}%`;
  const minorHeight = `${(minor / maxViolations) * 100}%`;

  return (
    <Card variant="outlined" sx={{ p: 3, height: 320, display: 'flex', flexDirection: 'column', bgcolor: 'background.paper' }}>
      <Stack component="div" direction="row" sx={{ justifyContent: 'space-between', alignItems: 'center', mb: 4 }}>
        <Typography variant="subtitle2" sx={{ fontWeight: '800', color: 'text.secondary', textTransform: 'uppercase', letterSpacing: '0.5px', fontSize: '0.72rem' }}>
          Critical Issues by Category
        </Typography>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.8 }}>
          <Box sx={{ width: 8, height: 8, bgcolor: 'success.main', borderRadius: '50%' }} />
          <Typography sx={{ fontSize: '0.72rem', fontWeight: '700', color: 'text.secondary' }}>WCAG 2.1</Typography>
        </Box>
      </Stack>

      {/* Premium Vertical Bar Chart */}
      <Stack component="div" direction="row" sx={{ justifyContent: 'space-around', alignItems: 'flex-end', flexGrow: 1, pb: 1, px: 2 }}>
        {/* Bar 1 */}
        <Stack component="div" spacing={1.5} sx={{ alignItems: 'center', height: '100%', justifyContent: 'flex-end', width: 60 }}>
          <Box sx={{ height: 130, width: 14, bgcolor: 'action.hover', borderRadius: '6px', position: 'relative', overflow: 'hidden' }}>
            <Box sx={{ position: 'absolute', bottom: 0, left: 0, right: 0, height: criticalHeight, bgcolor: 'error.main', borderRadius: '0 0 6px 6px' }} />
          </Box>
          <Typography sx={{ fontSize: '0.75rem', fontWeight: '700', color: 'text.secondary', whiteSpace: 'nowrap' }}>Level A ({critical})</Typography>
        </Stack>

        {/* Bar 2 */}
        <Stack component="div" spacing={1.5} sx={{ alignItems: 'center', height: '100%', justifyContent: 'flex-end', width: 60 }}>
          <Box sx={{ height: 130, width: 14, bgcolor: 'action.hover', borderRadius: '6px', position: 'relative', overflow: 'hidden' }}>
            <Box sx={{ position: 'absolute', bottom: 0, left: 0, right: 0, height: seriousHeight, bgcolor: 'warning.main', borderRadius: '0 0 6px 6px' }} />
          </Box>
          <Typography sx={{ fontSize: '0.75rem', fontWeight: '700', color: 'text.secondary', whiteSpace: 'nowrap' }}>Level AA ({serious})</Typography>
        </Stack>

        {/* Bar 3 */}
        <Stack component="div" spacing={1.5} sx={{ alignItems: 'center', height: '100%', justifyContent: 'flex-end', width: 60 }}>
          <Box sx={{ height: 130, width: 14, bgcolor: 'action.hover', borderRadius: '6px', position: 'relative', overflow: 'hidden' }}>
            <Box sx={{ position: 'absolute', bottom: 0, left: 0, right: 0, height: moderateHeight, bgcolor: 'secondary.main', borderRadius: '0 0 6px 6px' }} />
          </Box>
          <Typography sx={{ fontSize: '0.75rem', fontWeight: '700', color: 'text.secondary', whiteSpace: 'nowrap' }}>Level AAA ({moderate})</Typography>
        </Stack>

        {/* Bar 4 */}
        <Stack component="div" spacing={1.5} sx={{ alignItems: 'center', height: '100%', justifyContent: 'flex-end', width: 60 }}>
          <Box sx={{ height: 130, width: 14, bgcolor: 'action.hover', borderRadius: '6px', position: 'relative', overflow: 'hidden' }}>
            <Box sx={{ position: 'absolute', bottom: 0, left: 0, right: 0, height: minorHeight, bgcolor: 'primary.main', borderRadius: '0 0 6px 6px' }} />
          </Box>
          <Typography sx={{ fontSize: '0.75rem', fontWeight: '700', color: 'text.secondary', whiteSpace: 'nowrap' }}>BP ({minor})</Typography>
        </Stack>
      </Stack>
    </Card>
  );
};
