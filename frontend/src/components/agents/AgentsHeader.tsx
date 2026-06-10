import React from 'react';
import { Stack, Box, Typography, IconButton, alpha, useTheme } from '@mui/material';
import SmartToyIcon from '@mui/icons-material/SmartToy';
import RefreshIcon from '@mui/icons-material/Refresh';

interface AgentsHeaderProps {
  connected: boolean;
  onRefresh: () => void;
}

const AgentsHeader: React.FC<AgentsHeaderProps> = ({ connected, onRefresh }) => {
  const theme = useTheme();

  return (
    <Stack
      component="div"
      direction={{ xs: 'column', md: 'row' }}
      spacing={2}
      sx={{ justifyContent: 'space-between', alignItems: { xs: 'flex-start', md: 'center' }, mb: 4 }}
    >
      <Box>
        <Stack component="div" direction="row" spacing={1.5} sx={{ alignItems: 'center' }}>
          <SmartToyIcon color="primary" sx={{ fontSize: '2rem' }} />
          <Typography variant="h4" sx={{ fontWeight: '800', color: 'text.primary', letterSpacing: '-0.5px' }}>
            OpenClaw Agent Clusters
          </Typography>
        </Stack>
        <Typography variant="body2" color="text.secondary" sx={{ fontWeight: '500', mt: 0.5, pl: 0.5 }}>
          Real-time status indicators, active task parameters, and live worker stream log outputs.
        </Typography>
      </Box>

      <Stack component="div" direction="row" spacing={2} sx={{ alignItems: 'center' }}>
        {/* Connection Status Badge */}
        <Box
          sx={{
            display: 'flex',
            alignItems: 'center',
            gap: 1,
            px: 2,
            py: 0.75,
            borderRadius: '20px',
            bgcolor: alpha(connected ? theme.palette.success.main : theme.palette.error.main, 0.08),
            border: `1px solid ${alpha(connected ? theme.palette.success.main : theme.palette.error.main, 0.2)}`
          }}
        >
          <Box
            sx={{
              width: 8,
              height: 8,
              borderRadius: '50%',
              bgcolor: connected ? 'success.main' : 'error.main',
              animation: connected ? 'pulse 2s infinite' : 'none',
              '@keyframes pulse': {
                '0%': { transform: 'scale(0.95)', boxShadow: `0 0 0 0 ${alpha(theme.palette.success.main, 0.7)}` },
                '70%': { transform: 'scale(1)', boxShadow: `0 0 0 8px ${alpha(theme.palette.success.main, 0)}` },
                '100%': { transform: 'scale(0.95)', boxShadow: `0 0 0 0 ${alpha(theme.palette.success.main, 0)}` }
              }
            }}
          />
          <Typography variant="caption" sx={{ fontWeight: '700', color: connected ? 'success.main' : 'error.main', textTransform: 'uppercase', fontSize: '0.7rem', letterSpacing: '0.5px' }}>
            {connected ? 'Live Streaming' : 'Disconnected'}
          </Typography>
        </Box>

        <IconButton
          onClick={onRefresh}
          sx={{
            bgcolor: 'background.paper',
            border: '1px solid',
            borderColor: 'divider',
            '&:hover': { bgcolor: 'background.default' }
          }}
        >
          <RefreshIcon fontSize="small" />
        </IconButton>
      </Stack>
    </Stack>
  );
};

export default AgentsHeader;
