import React from 'react';
import {
  Card,
  Box,
  Typography,
  Stack,
  Chip,
  FormControlLabel,
  Switch,
  IconButton,
  alpha,
  useTheme
} from '@mui/material';
import TerminalIcon from '@mui/icons-material/Terminal';
import InfoIcon from '@mui/icons-material/Info';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import ErrorIcon from '@mui/icons-material/Error';
import ArrowForwardIcon from '@mui/icons-material/ArrowForward';
import type { LogItem } from './types';

interface AgentsTerminalProps {
  logs: LogItem[];
  logFilter: 'all' | 'spectre' | 'xray' | 'system';
  setLogFilter: (filter: 'all' | 'spectre' | 'xray' | 'system') => void;
  autoScroll: boolean;
  setAutoScroll: (autoScroll: boolean) => void;
  onClearLogs: () => void;
  terminalEndRef: React.RefObject<HTMLDivElement | null>;
}

const AgentsTerminal: React.FC<AgentsTerminalProps> = ({
  logs,
  logFilter,
  setLogFilter,
  autoScroll,
  setAutoScroll,
  onClearLogs,
  terminalEndRef
}) => {
  const theme = useTheme();

  // Filter logic
  const filteredLogs = logs.filter((log) => {
    if (logFilter === 'all') return true;
    if (logFilter === 'spectre') return log.agent.toLowerCase().includes('spectre');
    if (logFilter === 'xray') return log.agent.toLowerCase().includes('x-ray') || log.agent.toLowerCase().includes('xray');
    if (logFilter === 'system') return log.agent.toLowerCase() === 'system';
    return true;
  });

  return (
    <Card variant="outlined" sx={{ bgcolor: 'background.paper', overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
      {/* Terminal Header */}
      <Box sx={{ p: 2.5, borderBottom: '1px solid', borderColor: 'divider', display: 'flex', flexDirection: { xs: 'column', sm: 'row' }, justifyContent: 'space-between', alignItems: { xs: 'flex-start', sm: 'center' }, gap: 2 }}>
        <Stack component="div" direction="row" spacing={1.5} sx={{ alignItems: 'center' }}>
          <TerminalIcon sx={{ color: 'text.secondary' }} />
          <Box>
            <Typography variant="subtitle1" sx={{ fontWeight: '700' }}>
              Live Event Logs Stream
            </Typography>
            <Typography variant="caption" color="text.secondary">
              Real-time operational metrics reported by agent instances.
            </Typography>
          </Box>
        </Stack>

        {/* Log Filters */}
        <Stack component="div" direction="row" spacing={1} sx={{ alignItems: 'center', flexWrap: 'wrap', gap: 1 }}>
          {(['all', 'spectre', 'xray', 'system'] as const).map((filter) => (
            <Chip
              key={filter}
              label={filter.toUpperCase()}
              size="small"
              onClick={() => setLogFilter(filter)}
              sx={{
                fontWeight: '700',
                fontSize: '0.68rem',
                borderRadius: '6px',
                cursor: 'pointer',
                bgcolor: logFilter === filter ? 'primary.main' : 'background.default',
                color: logFilter === filter ? 'primary.contrastText' : 'text.secondary',
                border: '1px solid',
                borderColor: logFilter === filter ? 'primary.main' : 'divider',
                '&:hover': {
                  bgcolor: logFilter === filter ? 'primary.dark' : alpha(theme.palette.primary.main, 0.05)
                }
              }}
            />
          ))}
          
          <Box sx={{ width: '1px', height: '24px', bgcolor: 'divider', mx: 1 }} />

          <FormControlLabel
            control={
              <Switch
                size="small"
                checked={autoScroll}
                onChange={(e) => setAutoScroll(e.target.checked)}
                color="primary"
              />
            }
            label={
              <Typography variant="caption" sx={{ fontWeight: '600', color: 'text.secondary' }}>
                Auto-scroll
              </Typography>
            }
            sx={{ mr: 1 }}
          />

          <IconButton size="small" onClick={onClearLogs} title="Clear terminal window">
            <Typography variant="caption" sx={{ fontWeight: '700', color: 'text.disabled', '&:hover': { color: 'error.main' } }}>
              CLEAR
            </Typography>
          </IconButton>
        </Stack>
      </Box>

      {/* Terminal Window */}
      <Box
        sx={{
          bgcolor: '#0f172a',
          p: 3,
          height: '400px',
          overflowY: 'auto',
          fontFamily: 'Consolas, Monaco, "Courier New", monospace',
          fontSize: '0.85rem',
          lineHeight: 1.6,
          color: '#f8fafc',
          display: 'flex',
          flexDirection: 'column-reverse' // Keeps scrolled to bottom cleanly
        }}
      >
        <div ref={terminalEndRef} />
        
        {filteredLogs.length === 0 ? (
          <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%', color: 'text.disabled' }}>
            <TerminalIcon sx={{ fontSize: '3rem', mb: 1.5, opacity: 0.15, color: '#94a3b8' }} />
            <Typography variant="body2" sx={{ fontFamily: 'inherit', color: '#64748b' }}>
              No events registered in log buffer.
            </Typography>
          </Box>
        ) : (
          filteredLogs.map((log, index) => {
            let badgeColor = '#60a5fa'; // Blue (info)
            let textColor = '#f8fafc'; // White
            let icon = <InfoIcon sx={{ fontSize: '0.9rem', mr: 0.75, color: 'inherit' }} />;

            if (log.type === 'success') {
              badgeColor = '#34d399'; // Green (success)
              textColor = '#a7f3d0';
              icon = <CheckCircleIcon sx={{ fontSize: '0.9rem', mr: 0.75, color: 'inherit' }} />;
            } else if (log.type === 'error') {
              badgeColor = '#fb7185'; // Red (error)
              textColor = '#fecdd3';
              icon = <ErrorIcon sx={{ fontSize: '0.9rem', mr: 0.75, color: 'inherit' }} />;
            }

            return (
              <Box
                key={index}
                sx={{
                  py: 0.75,
                  px: 1.5,
                  borderRadius: '6px',
                  mb: 1,
                  bgcolor: alpha(badgeColor, 0.03),
                  borderLeft: `3px solid ${badgeColor}`,
                  display: 'flex',
                  flexDirection: { xs: 'column', md: 'row' },
                  alignItems: { xs: 'flex-start', md: 'center' },
                  gap: { xs: 0.5, md: 1.5 },
                  animation: 'fadeIn 0.2s ease-out',
                  '@keyframes fadeIn': {
                    from: { opacity: 0, transform: 'translateY(4px)' },
                    to: { opacity: 1, transform: 'translateY(0)' }
                  }
                }}
              >
                {/* Time and Badge */}
                <Stack component="div" direction="row" spacing={1.5} sx={{ alignItems: 'center', minWidth: '220px' }}>
                  <Typography variant="caption" sx={{ color: '#64748b', fontFamily: 'inherit' }}>
                    [{log.time}]
                  </Typography>
                  <Box
                    sx={{
                      px: 1,
                      py: 0.25,
                      borderRadius: '4px',
                      bgcolor: alpha(badgeColor, 0.15),
                      color: badgeColor,
                      fontSize: '0.7rem',
                      fontWeight: '800',
                      letterSpacing: '0.5px',
                      textTransform: 'uppercase',
                      fontFamily: 'inherit'
                    }}
                  >
                    {log.agent}
                  </Box>
                </Stack>

                {/* Log Message */}
                <Box sx={{ display: 'flex', alignItems: 'center', flexGrow: 1, color: textColor }}>
                  {icon}
                  <Typography variant="body2" sx={{ fontFamily: 'inherit', color: 'inherit' }}>
                    {log.message}
                  </Typography>
                </Box>

                {/* Context Link */}
                {log.task_id && (
                  <Box
                    onClick={() => window.open(`http://localhost:8002/report/${log.task_id}`, '_blank')}
                    sx={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: 0.5,
                      color: '#64748b',
                      cursor: 'pointer',
                      '&:hover': { color: 'primary.main' }
                    }}
                  >
                    <Typography variant="caption" sx={{ fontFamily: 'inherit', textDecoration: 'underline' }}>
                      View Report
                    </Typography>
                    <ArrowForwardIcon sx={{ fontSize: '0.8rem' }} />
                  </Box>
                )}
              </Box>
            );
          })
        )}
      </Box>
    </Card>
  );
};

export default AgentsTerminal;
