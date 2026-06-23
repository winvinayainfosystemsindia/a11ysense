import React from 'react';
import { Box, Card, Stack, Typography, LinearProgress, useTheme } from '@mui/material';
import AssessmentIcon from '@mui/icons-material/Assessment';
import ErrorIcon from '@mui/icons-material/Error';
import TravelExploreIcon from '@mui/icons-material/TravelExplore';
import BugReportIcon from '@mui/icons-material/BugReport';

interface CompletedViewDashboardProps {
  accessibilityScore: number;
  criticalCount: number;
  totalIssuesCount: number;
  pagesScannedCount: number;
  pagesDiscoveredCount: number;
}

export const CompletedViewDashboard: React.FC<CompletedViewDashboardProps> = ({
  accessibilityScore,
  criticalCount,
  totalIssuesCount,
  pagesScannedCount,
  pagesDiscoveredCount
}) => {
  const theme = useTheme();

  return (
    <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: 'repeat(2, 1fr)', md: 'repeat(4, 1fr)' }, gap: 3 }}>
      {/* Score Card */}
      <Card variant="outlined" sx={{ p: 3, borderRadius: '16px', borderLeft: `6px solid ${accessibilityScore >= 80 ? theme.palette.success.main : accessibilityScore >= 70 ? theme.palette.warning.main : theme.palette.error.main}` }}>
        <Stack component="div" direction="row" spacing={1.5} sx={{ alignItems: 'center', mb: 1.5 }}>
          <AssessmentIcon color="primary" />
          <Typography variant="overline" sx={{ fontWeight: '800', color: 'text.secondary', fontSize: '0.7rem' }}>Accessibility Score</Typography>
        </Stack>
        <Box sx={{ display: 'flex', alignItems: 'baseline', gap: 0.5, mb: 1.5 }}>
          <Typography variant="h3" sx={{ fontWeight: '800', color: accessibilityScore >= 80 ? 'success.main' : accessibilityScore >= 70 ? 'warning.main' : 'error.main' }}>
            {accessibilityScore.toFixed(0)}
          </Typography>
          <Typography variant="h6" color="text.secondary">/ 100</Typography>
        </Box>
        <LinearProgress
          variant="determinate"
          value={accessibilityScore}
          sx={{ height: 6, borderRadius: 3, bgcolor: '#e2e8f0', '& .MuiLinearProgress-bar': { bgcolor: accessibilityScore >= 80 ? 'success.main' : accessibilityScore >= 70 ? 'warning.main' : 'error.main', borderRadius: 3 } }}
        />
        <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
          % of accessibility checks passed
        </Typography>
      </Card>

      {/* Pages Scanned Card */}
      <Card variant="outlined" sx={{ p: 3, borderRadius: '16px', borderLeft: `6px solid ${theme.palette.info.main}` }}>
        <Stack component="div" direction="row" spacing={1.5} sx={{ alignItems: 'center', mb: 1.5 }}>
          <TravelExploreIcon color="info" />
          <Typography variant="overline" sx={{ fontWeight: '800', color: 'text.secondary', fontSize: '0.7rem' }}>Pages Scanned</Typography>
        </Stack>
        <Typography variant="h3" sx={{ fontWeight: '800', color: 'info.main', mb: 0.5 }}>
          {pagesScannedCount}
        </Typography>
        <Typography variant="caption" color="text.secondary">
          {pagesDiscoveredCount > pagesScannedCount ? `Of ${pagesDiscoveredCount} pages discovered` : 'Pages covered in this audit'}
        </Typography>
      </Card>

      {/* Critical Issues Card */}
      <Card variant="outlined" sx={{ p: 3, borderRadius: '16px', borderLeft: `6px solid ${theme.palette.error.main}` }}>
        <Stack component="div" direction="row" spacing={1.5} sx={{ alignItems: 'center', mb: 1.5 }}>
          <ErrorIcon color="error" />
          <Typography variant="overline" sx={{ fontWeight: '800', color: 'text.secondary', fontSize: '0.7rem' }}>Critical Issues</Typography>
        </Stack>
        <Typography variant="h3" sx={{ fontWeight: '800', color: 'error.main', mb: 0.5 }}>
          {criticalCount}
        </Typography>
        <Typography variant="caption" color="text.secondary">Requires immediate attention</Typography>
      </Card>

      {/* Total Issues Card */}
      <Card variant="outlined" sx={{ p: 3, borderRadius: '16px', borderLeft: `6px solid ${theme.palette.warning.main}` }}>
        <Stack component="div" direction="row" spacing={1.5} sx={{ alignItems: 'center', mb: 1.5 }}>
          <BugReportIcon color="warning" />
          <Typography variant="overline" sx={{ fontWeight: '800', color: 'text.secondary', fontSize: '0.7rem' }}>Total Issues Found</Typography>
        </Stack>
        <Typography variant="h3" sx={{ fontWeight: '800', color: 'warning.main', mb: 0.5 }}>
          {totalIssuesCount}
        </Typography>
        <Typography variant="caption" color="text.secondary">Across all severities</Typography>
      </Card>
    </Box>
  );
};
