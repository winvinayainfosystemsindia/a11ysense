import React from 'react';
import {
  Box,
  Typography,
  Stack,
  Card,
  CardContent,
  Divider,
  useTheme,
} from '@mui/material';
import { alpha } from '@mui/material/styles';
import type { EstimationSummary } from '../../service/estimationService';

interface ComplexityDistributionCardProps {
  summary: EstimationSummary;
}

export const ComplexityDistributionCard: React.FC<ComplexityDistributionCardProps> = ({ summary }) => {
  const theme = useTheme();

  const totalPages = summary.total_pages || 0;
  const simplePct = totalPages > 0 ? (summary.simple_pages / totalPages) * 100 : 0;
  const mediumPct = totalPages > 0 ? (summary.medium_pages / totalPages) * 100 : 0;
  const complexPct = totalPages > 0 ? (summary.complex_pages / totalPages) * 100 : 0;

  return (
    <Card
      sx={{
        mb: 4,
        borderRadius: 4,
        border: '1px solid',
        borderColor: theme.palette.divider,
        overflow: 'hidden',
        boxShadow: `0 2px 12px ${alpha(theme.palette.text.primary, 0.04)}`,
        bgcolor: theme.palette.background.paper,
      }}
    >
      <CardContent sx={{ p: 3 }}>
        {/* Distribution Bar */}
        <Box sx={{ mb: 2 }}>
          <Stack component="div" direction="row" sx={{ justifyContent: 'space-between', mb: 1 }}>
            <Typography variant="caption" sx={{ fontWeight: 800, color: 'text.secondary', textTransform: 'uppercase' }}>
              Complexity Tier Distribution
            </Typography>
            <Typography variant="caption" sx={{ fontWeight: 700, color: 'text.secondary' }}>
              {totalPages} Total Page(s)
            </Typography>
          </Stack>
          <Box
            sx={{
              display: 'flex',
              height: 10,
              borderRadius: 5,
              overflow: 'hidden',
              bgcolor: alpha(theme.palette.text.primary, 0.06),
            }}
          >
            {simplePct > 0 && (
              <Box sx={{ width: `${simplePct}%`, bgcolor: theme.palette.success.main }} />
            )}
            {mediumPct > 0 && (
              <Box sx={{ width: `${mediumPct}%`, bgcolor: theme.palette.warning.main }} />
            )}
            {complexPct > 0 && (
              <Box sx={{ width: `${complexPct}%`, bgcolor: theme.palette.error.main }} />
            )}
          </Box>
        </Box>

        <Divider sx={{ my: 2 }} />

        <Stack
          component="div"
          direction={{ xs: 'column', sm: 'row' }}
          spacing={3}
          sx={{ alignItems: 'center', justifyContent: 'space-around' }}
        >
          <Box sx={{ textAlign: 'center' }}>
            <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 700 }}>
              TOTAL PAGES AUDITED
            </Typography>
            <Typography variant="h5" sx={{ fontWeight: 800, color: theme.palette.text.primary }}>
              {totalPages}
            </Typography>
          </Box>
          <Divider orientation="vertical" flexItem />
          <Box sx={{ textAlign: 'center' }}>
            <Typography variant="caption" sx={{ color: theme.palette.success.dark, fontWeight: 700 }}>
              SIMPLE PAGES (1.0H)
            </Typography>
            <Typography variant="h5" sx={{ fontWeight: 800, color: theme.palette.success.main }}>
              {summary.simple_pages}
            </Typography>
          </Box>
          <Divider orientation="vertical" flexItem />
          <Box sx={{ textAlign: 'center' }}>
            <Typography variant="caption" sx={{ color: theme.palette.warning.dark, fontWeight: 700 }}>
              MEDIUM PAGES (2.5H)
            </Typography>
            <Typography variant="h5" sx={{ fontWeight: 800, color: theme.palette.warning.main }}>
              {summary.medium_pages}
            </Typography>
          </Box>
          <Divider orientation="vertical" flexItem />
          <Box sx={{ textAlign: 'center' }}>
            <Typography variant="caption" sx={{ color: theme.palette.error.dark, fontWeight: 700 }}>
              COMPLEX PAGES (5.5H)
            </Typography>
            <Typography variant="h5" sx={{ fontWeight: 800, color: theme.palette.error.main }}>
              {summary.complex_pages}
            </Typography>
          </Box>
        </Stack>
      </CardContent>
    </Card>
  );
};
