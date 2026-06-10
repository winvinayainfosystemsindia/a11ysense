import React from 'react';
import { Box, Typography, Stack, useTheme } from '@mui/material';
import { alpha } from '@mui/material/styles';
import RefreshIcon from '@mui/icons-material/Refresh';
import { useAppSelector } from '../../store';
import { Button } from '../common/button';

interface WelcomeHeaderProps {
  orgName: string;
  timeRange: '24h' | '7d' | '30d';
  onTimeRangeChange: (range: '24h' | '7d' | '30d') => void;
  onSync: () => void;
}

export const WelcomeHeader: React.FC<WelcomeHeaderProps> = ({
  orgName,
  timeRange,
  onTimeRangeChange,
  onSync
}) => {
  const theme = useTheme();
  const { user } = useAppSelector((state) => state.auth);

  const getGreeting = () => {
    const hour = new Date().getHours();
    if (hour < 12) return 'Good Morning';
    if (hour < 17) return 'Good Afternoon';
    return 'Good Evening';
  };

  const formattedDate = new Intl.DateTimeFormat('en-US', {
    weekday: 'long',
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  }).format(new Date());

  const userEmail = user?.email || localStorage.getItem('user_email') || 'daran@winvinaya.com';
  let displayName = userEmail.split('@')[0];
  if (displayName.toLowerCase() === 'daran') {
    displayName = 'Dharanidaran';
  } else {
    displayName = displayName
      .replace(/[._-]/g, ' ')
      .split(' ')
      .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ');
  }

  const cleanOrg = orgName.includes('WinVinaya') ? 'WinVinaya' : orgName;

  return (
    <Box sx={{
      mb: 4,
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
      flexWrap: 'wrap',
      gap: 2
    }}>
      <Box>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
          <Typography variant="h4" sx={{ fontWeight: 700, color: '#16191f', letterSpacing: '-0.02em', fontSize: { xs: '1.5rem', md: '1.875rem' } }}>
            {getGreeting()}, {displayName}! 👋
          </Typography>
        </Box>
        <Typography variant="body1" sx={{ color: '#545b64', fontWeight: 500, fontSize: { xs: '0.875rem', md: '1.0rem' } }}>
          Welcome back to the {cleanOrg}. Here's what's happening today, {formattedDate}.
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
    </Box>
  );
};
