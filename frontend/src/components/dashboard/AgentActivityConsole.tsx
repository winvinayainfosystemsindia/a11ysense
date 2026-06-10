import React, { useState, useEffect, useRef } from 'react';
import { Card, Stack, Box, Typography, useTheme } from '@mui/material';
import { alpha } from '@mui/material/styles';
import { useNavigate } from '@tanstack/react-router';
import type { DashboardStats as StatsType } from '../../model/dashboard.model';
import { ENV } from '../../config/env';

interface LogItem {
  time: string;
  agent: string;
  message: string;
  type: 'success' | 'info' | 'error';
  task_id: string;
  status: string;
  pages_completed?: number;
  pages_total?: number;
}

interface AgentActivityConsoleProps {
  stats: StatsType | null;
  onNavigateToAudit: () => void;
}

const getProjectNameFromUrl = (urlStr: string): string => {
  try {
    const cleanUrl = urlStr.replace(/^(https?:\/\/)?(www\.)?/, '');
    const firstPart = cleanUrl.split('/')[0];
    const parts = firstPart.split('.');
    if (parts.length > 1) {
      return parts[parts.length - 2].charAt(0).toUpperCase() + parts[parts.length - 2].slice(1) + ' Flow';
    }
    return firstPart || 'Audit Flow';
  } catch (e) {
    return 'Audit Flow';
  }
};

export const AgentActivityConsole: React.FC<AgentActivityConsoleProps> = ({
  stats
}) => {
  const theme = useTheme();
  const navigate = useNavigate();
  const terminalRef = useRef<HTMLDivElement>(null);

  const [logs, setLogs] = useState<LogItem[]>([]);
  const [connected, setConnected] = useState<boolean>(false);

  const recentAudits = stats?.recent_audits || [];
  const orgId = localStorage.getItem('org_id') || 'default';

  // Helper to generate fallback logs from recentAudits if SSE is empty/offline
  const getLogsFromAudits = (audits: any[]): LogItem[] => {
    if (!audits || audits.length === 0) {
      return [
        {
          time: new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false }),
          agent: 'System',
          message: 'No active crawler agents running.',
          type: 'info',
          task_id: '',
          status: 'idle'
        }
      ];
    }
    return audits.slice(0, 5).map((audit) => {
      const timeStr = new Date(audit.timestamp).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false });
      const projName = audit.project_name || getProjectNameFromUrl(audit.url);

      if (audit.status === 'completed') {
        return {
          time: timeStr,
          agent: 'System',
          message: `Audit completed for ${projName} with score ${audit.accessibility_score} (${audit.total_violations} violations)`,
          type: 'success',
          task_id: audit.task_id,
          status: audit.status
        };
      } else if (audit.status === 'failed') {
        return {
          time: timeStr,
          agent: 'System',
          message: `Audit failed for ${projName}. Please check crawler configuration.`,
          type: 'error',
          task_id: audit.task_id,
          status: audit.status
        };
      } else {
        return {
          time: timeStr,
          agent: 'Agent X-Ray',
          message: `Auditing ${projName} - scanning DOM tree...`,
          type: 'info',
          task_id: audit.task_id,
          status: audit.status
        };
      }
    });
  };

  useEffect(() => {
    const token = localStorage.getItem('auth_token');
    if (!token) return;

    const streamUrl = `${ENV.API_URL}/agents/telemetry/stream?token=${encodeURIComponent(token)}`;
    const eventSource = new EventSource(streamUrl);

    eventSource.onopen = () => {
      setConnected(true);
      const timeStr = new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false });
      setLogs((prev) => {
        const connLog: LogItem = {
          time: timeStr,
          agent: 'System',
          message: 'Connected to live telemetry gateway.',
          type: 'success',
          task_id: '',
          status: 'connected'
        };
        // Avoid adding duplicate connection messages in rapid succession
        if (prev.length > 0 && prev[0].status === 'connected') {
          return prev;
        }
        return [connLog, ...prev].slice(0, 50);
      });
    };

    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.error) {
          throw new Error(data.error);
        }

        setLogs((prev) => {
          // Deduplicate identical sequential stream updates to keep console clean
          const lastLog = prev[0];
          if (
            lastLog &&
            lastLog.task_id === data.task_id &&
            lastLog.status === data.status &&
            lastLog.pages_completed === data.pages_completed &&
            lastLog.message === data.message
          ) {
            return prev;
          }

          // Prepend new logs to the beginning of the array since we render in column-reverse
          return [data, ...prev].slice(0, 50);
        });
      } catch (err: any) {
        console.error('Error parsing SSE event:', err);
      }
    };

    eventSource.onerror = (err) => {
      console.error('SSE connection error:', err);
      setConnected(false);
    };

    return () => {
      eventSource.close();
    };
  }, []);

  // Use live logs if connected and we have received them, else fallback to historical audits
  const displayLogs = logs.length > 0 ? logs : getLogsFromAudits(recentAudits);

  return (
    <Card variant="outlined" sx={{ p: 3, height: 320, display: 'flex', flexDirection: 'column', bgcolor: 'background.paper' }}>
      <Stack component="div" direction="row" sx={{ justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="subtitle2" sx={{ fontWeight: '800', color: 'text.secondary', textTransform: 'uppercase', letterSpacing: '0.5px', fontSize: '0.72rem' }}>
          OpenClaw Agent Activity
        </Typography>
        <Box sx={{
          display: 'inline-flex',
          alignItems: 'center',
          bgcolor: (theme) => alpha(connected ? theme.palette.success.main : theme.palette.error.main, 0.12),
          px: 1,
          py: 0.25,
          borderRadius: '6px',
          gap: 0.5,
          border: `1px solid ${alpha(connected ? theme.palette.success.main : theme.palette.error.main, 0.2)}`
        }}>
          <Box sx={{
            width: 6,
            height: 6,
            bgcolor: connected ? 'success.main' : 'error.main',
            borderRadius: '50%',
            animation: connected ? 'pulse 1.5s infinite' : 'none'
          }} />
          <Typography sx={{ fontSize: '0.62rem', fontWeight: '800', color: connected ? 'success.main' : 'error.main' }}>
            {connected ? 'LIVE' : 'OFFLINE'}
          </Typography>
        </Box>
      </Stack>

      {/* Terminal Console log window */}
      <Box
        ref={terminalRef}
        sx={{
          flexGrow: 1,
          bgcolor: '#0f172a',
          p: 2,
          borderRadius: '10px',
          fontFamily: 'Consolas, Monaco, "Courier New", monospace',
          fontSize: '0.72rem',
          lineHeight: 1.5,
          overflowY: 'auto',
          display: 'flex',
          flexDirection: 'column-reverse',
          boxShadow: 'inset 0 2px 8px rgba(0,0,0,0.2)',
          color: '#f8fafc'
        }}
      >
        <div style={{ height: 1 }} />
        {displayLogs.map((log, idx) => {
          let badgeColor = '#60a5fa'; // Blue (info)
          let textColor = '#f8fafc'; // White/light grey

          if (log.type === 'success') {
            badgeColor = '#34d399'; // Green (success)
            textColor = '#a7f3d0';
          } else if (log.type === 'error') {
            badgeColor = '#fb7185'; // Red (error)
            textColor = '#fecdd3';
          }

          return (
            <Box key={idx} sx={{
              mb: 1,
              display: 'flex',
              alignItems: 'flex-start',
              gap: 1,
              borderLeft: `2px solid ${badgeColor}`,
              pl: 1,
              py: 0.25,
            }}>
              <Box component="span" sx={{ color: '#64748b', whiteSpace: 'nowrap' }}>[{log.time}]</Box>
              <Box component="span" sx={{ color: badgeColor, fontWeight: '700', whiteSpace: 'nowrap' }}>{log.agent}:</Box>
              <Box component="span" sx={{ color: textColor, flexGrow: 1, wordBreak: 'break-all' }}>{log.message}</Box>
            </Box>
          );
        })}
      </Box>

      {/* Console Toolbar Footer */}
      <Stack component="div" direction="row" sx={{ justifyContent: 'space-between', alignItems: 'center', mt: 2, pt: 1.5, borderTop: `1px solid ${alpha(theme.palette.divider, 0.1)}` }}>
        <Typography sx={{ fontFamily: 'monospace', fontSize: '0.7rem', color: 'text.secondary', fontWeight: '700' }}>
          {stats?.active_audits_count || 0} Active Processes
        </Typography>
        <Typography
          onClick={() => navigate({ to: '/org/$orgId/agents', params: { orgId } })}
          sx={{
            fontFamily: 'monospace',
            fontSize: '0.7rem',
            color: 'primary.main',
            fontWeight: '700',
            cursor: 'pointer',
            textDecoration: 'none',
            '&:hover': { textDecoration: 'underline' }
          }}
        >
          View Agent Cluster
        </Typography>
      </Stack>

      {/* Keyframe animation declarations */}
      <style>
        {`
          @keyframes pulse {
            0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(5, 150, 105, 0.4); }
            70% { transform: scale(1); box-shadow: 0 0 0 6px rgba(5, 150, 105, 0); }
            100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(5, 150, 105, 0); }
          }
        `}
      </style>
    </Card>
  );
};
