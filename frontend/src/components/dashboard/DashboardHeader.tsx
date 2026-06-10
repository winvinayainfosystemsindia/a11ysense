import React from 'react';
import { Box, Typography, Stack, useTheme } from '@mui/material';
import { alpha } from '@mui/material/styles';
import RefreshIcon from '@mui/icons-material/Refresh';
import { Button } from '../common/button';

interface DashboardHeaderProps {
  orgName: string;
  timeRange: '24h' | '7d' | '30d';
  onTimeRangeChange: (range: '24h' | '7d' | '30d') => void;
  onSync: () => void;
}

export const DashboardHeader: React.FC<DashboardHeaderProps> = ({
  orgName,
  timeRange,
  onTimeRangeChange,
  onSync
}) => {
  const theme = useTheme();

  return (
    <Stack
      component="div"
      direction={{ xs: 'column', md: 'row' }}
      spacing={2}
      sx={{ justifyContent: 'space-between', alignItems: { xs: 'flex-start', md: 'center' } }}
    >
      <Box>
        <Typography variant="h4" sx={{ fontWeight: '800', color: 'text.primary', letterSpacing: '-0.5px' }}>
          {orgName} Workspace
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ fontWeight: '500', mt: 0.5 }}>
          Real-time autonomous accessibility audit insights and agent telemetry.
        </Typography>
      </Box>

      <Stack component="div" direction="row" spacing={2} sx={{ alignItems: 'center', width: { xs: '100%', md: 'auto' }, justifyContent: { xs: 'space-between', md: 'flex-end' } }}>
        {/* Time Selector Group */}
        <Box sx={{
          display: 'flex',
          p: 0.5,
          bgcolor: 'background.default',
          border: '1px solid',
          borderColor: 'divider',
          borderRadius: '10px'
        }}>
          {(['24h', '7d', '30d'] as const).map((range) => {
            const active = timeRange === range;
            const labelMap = { '24h': 'Last 24h', '7d': '7 Days', '30d': '30 Days' };
            return (
              <Button
                key={range}
                size="small"
                onClick={() => onTimeRangeChange(range)}
                sx={{
                  px: 2,
                  py: 0.75,
                  borderRadius: '8px',
                  textTransform: 'none',
                  fontWeight: active ? '700' : '500',
                  fontSize: '0.8rem',
                  bgcolor: active ? 'background.paper' : 'transparent',
                  color: active ? 'primary.main' : 'text.secondary',
                  boxShadow: active ? '0 1px 3px rgba(0,0,0,0.05)' : 'none',
                  '&:hover': {
                    bgcolor: active ? 'background.paper' : alpha(theme.palette.primary.main, 0.04)
                  }
                }}
              >
                {labelMap[range]}
              </Button>
            );
          })}
        </Box>

        {/* Sync Stats Button */}
        <Button
          variant="outlined"
          onClick={onSync}
          startIcon={<RefreshIcon />}
          sx={{
            fontWeight: '700',
            borderRadius: '8px',
            borderColor: 'divider',
            color: 'text.secondary',
            height: '38px',
            '&:hover': { bgcolor: 'background.default', borderColor: 'text.disabled' }
          }}
        >
          Sync Stats
        </Button>
      </Stack>
    </Stack>
  );
};
