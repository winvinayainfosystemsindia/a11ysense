import React from 'react';
import { Box, Card, Stack, Typography, LinearProgress, useTheme } from '@mui/material';
import AssessmentIcon from '@mui/icons-material/Assessment';
import ErrorIcon from '@mui/icons-material/Error';
import WarningIcon from '@mui/icons-material/Warning';
import LayersIcon from '@mui/icons-material/Layers';
import type { AuditTaskDetail } from '../../../service/auditService';

interface CompletedViewDashboardProps {
  accessibilityScore: number;
  criticalCount: number;
  moderateCount: number;
  taskDetail: AuditTaskDetail;
}

export const CompletedViewDashboard: React.FC<CompletedViewDashboardProps> = ({
  accessibilityScore,
  criticalCount,
  moderateCount,
  taskDetail
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

      {/* Moderate Issues Card */}
      <Card variant="outlined" sx={{ p: 3, borderRadius: '16px', borderLeft: `6px solid ${theme.palette.warning.main}` }}>
        <Stack component="div" direction="row" spacing={1.5} sx={{ alignItems: 'center', mb: 1.5 }}>
          <WarningIcon color="warning" />
          <Typography variant="overline" sx={{ fontWeight: '800', color: 'text.secondary', fontSize: '0.7rem' }}>Moderate Issues</Typography>
        </Stack>
        <Typography variant="h3" sx={{ fontWeight: '800', color: 'warning.main', mb: 0.5 }}>
          {moderateCount}
        </Typography>
        <Typography variant="caption" color="text.secondary">Improvement recommended</Typography>
      </Card>

      {/* Crawl Depth Card */}
      <Card variant="outlined" sx={{ p: 3, borderRadius: '16px', borderLeft: `6px solid ${theme.palette.info.main}` }}>
        <Stack component="div" direction="row" spacing={1.5} sx={{ alignItems: 'center', mb: 1.5 }}>
          <LayersIcon color="info" />
          <Typography variant="overline" sx={{ fontWeight: '800', color: 'text.secondary', fontSize: '0.7rem' }}>Crawl Depth</Typography>
        </Stack>
        <Typography variant="h3" sx={{ fontWeight: '800', color: 'info.main', mb: 0.5 }}>
          {taskDetail.depth ?? 1}
        </Typography>
        <Typography variant="caption" color="text.secondary">Maximum crawl limit</Typography>
      </Card>
    </Box>
  );
};
