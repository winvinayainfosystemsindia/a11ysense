import React, { useState, useEffect, useRef } from 'react';
import { Box, CircularProgress, Stack } from '@mui/material';
import { useNavigate } from '@tanstack/react-router';

import api from '../../service/api';
import { ENV } from '../../config/env';
import type { LogItem, TelemetryStats } from '../../components/agents/types';
import AgentsHeader from '../../components/agents/AgentsHeader';
import AgentsStatsGrid from '../../components/agents/AgentsStatsGrid';
import AgentsTopology from '../../components/agents/AgentsTopology';
import AgentsTerminal from '../../components/agents/AgentsTerminal';

const AgentsConsole: React.FC = () => {
  const navigate = useNavigate();
  const terminalEndRef = useRef<HTMLDivElement>(null);

  const [stats, setStats] = useState<TelemetryStats | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [logs, setLogs] = useState<LogItem[]>([]);
  const [logFilter, setLogFilter] = useState<'all' | 'spectre' | 'xray' | 'system'>('all');
  const [autoScroll, setAutoScroll] = useState<boolean>(true);
  const [connected, setConnected] = useState<boolean>(false);

  // Fetch initial telemetry stats
  const fetchTelemetry = async () => {
    try {
      const response = await api.get('/agents/telemetry');
      setStats(response.data);
    } catch (err) {
      console.error('Failed to load telemetry stats:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!localStorage.getItem('auth_token')) {
      navigate({ to: '/auth/signin' });
      return;
    }

    fetchTelemetry();

    // Set up SSE EventSource stream connection
    const token = localStorage.getItem('auth_token') || '';
    const streamUrl = `${ENV.API_URL}/agents/telemetry/stream?token=${encodeURIComponent(token)}`;
    const eventSource = new EventSource(streamUrl);

    eventSource.onopen = () => {
      setConnected(true);
      // Prepend system connection log
      const timeStr = new Date().toLocaleTimeString();
      setLogs((prev) => [
        {
          time: timeStr,
          agent: 'System',
          message: 'Telemetry Gateway connection established successfully. Subscribed to live stream.',
          type: 'success',
          task_id: '',
          status: 'connected'
        },
        ...prev
      ]);
    };

    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.error) {
          throw new Error(data.error);
        }

        // Add to log console (maintain max 150 entries for DOM speed)
        setLogs((prev) => {
          const updated = [data, ...prev];
          if (updated.length > 150) {
            return updated.slice(0, 150);
          }
          return updated;
        });

        // Trigger telemetry update dynamically upon worker state changes
        fetchTelemetry();
      } catch (err: any) {
        console.error('Error parsing SSE event:', err);
        setLogs((prev) => [
          {
            time: new Date().toLocaleTimeString(),
            agent: 'System',
            message: `Stream parsing error: ${err.message || 'Malformed event packet'}`,
            type: 'error',
            task_id: '',
            status: 'error'
          },
          ...prev
        ]);
      }
    };

    eventSource.onerror = (err) => {
      console.error('SSE connection error:', err);
      setConnected(false);
      setLogs((prev) => [
        {
          time: new Date().toLocaleTimeString(),
          agent: 'System',
          message: 'Telemetry Gateway disconnected. Attempting auto-reconnect...',
          type: 'error',
          task_id: '',
          status: 'disconnected'
        },
        ...prev
      ]);
    };

    return () => {
      eventSource.close();
    };
  }, [navigate]);

  // Scroll to bottom of terminal if autoScroll is enabled
  useEffect(() => {
    if (autoScroll && terminalEndRef.current) {
      terminalEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [logs, autoScroll]);

  const handleClearLogs = () => {
    setLogs([]);
  };

  return (
    <Box sx={{ pb: 4 }}>
      <AgentsHeader connected={connected} onRefresh={fetchTelemetry} />

      {loading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '300px' }}>
          <CircularProgress size={50} color="primary" />
        </Box>
      ) : (
        <Stack component="div" spacing={4} sx={{ width: '100%' }}>
          <AgentsStatsGrid stats={stats} />
          
          <AgentsTopology stats={stats} />

          <AgentsTerminal
            logs={logs}
            logFilter={logFilter}
            setLogFilter={setLogFilter}
            autoScroll={autoScroll}
            setAutoScroll={setAutoScroll}
            onClearLogs={handleClearLogs}
            terminalEndRef={terminalEndRef}
          />
        </Stack>
      )}
    </Box>
  );
};

export default AgentsConsole;
