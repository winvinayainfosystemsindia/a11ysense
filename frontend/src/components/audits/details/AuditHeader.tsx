import React from 'react';
import { Box, Stack, Typography, Chip, Button } from '@mui/material';
import LaunchIcon from '@mui/icons-material/Launch';
import FileDownloadIcon from '@mui/icons-material/FileDownload';
import PauseIcon from '@mui/icons-material/Pause';
import StopIcon from '@mui/icons-material/Stop';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import type { AuditTaskDetail } from '../../../service/auditService';

interface AuditHeaderProps {
  taskId: string;
  taskDetail: AuditTaskDetail;
  isCompleted: boolean;
  isStopped: boolean;
  isRunning: boolean;
  isPaused: boolean;
  actionLoading: boolean;
  handleOpenReport: () => void;
  handleExportReport: () => void;
  handlePause: () => void;
  handleResume: () => void;
  handleStop: () => void;
}

export const AuditHeader: React.FC<AuditHeaderProps> = ({
  taskId,
  taskDetail,
  isCompleted,
  isStopped,
  isRunning,
  isPaused,
  actionLoading,
  handleOpenReport,
  handleExportReport,
  handlePause,
  handleResume,
  handleStop
}) => {
  return (
    <Stack
      component="div"
      direction={{ xs: 'column', md: 'row' }}
      spacing={3}
      sx={{ justifyContent: 'space-between', alignItems: { xs: 'flex-start', md: 'center' }, mb: 4 }}
    >
      <Box>
        <Stack component="div" direction="row" spacing={2} sx={{ alignItems: 'center', mb: 1 }}>
          <Typography variant="h4" sx={{ fontWeight: '800', letterSpacing: '-0.5px' }}>
            Audit #{taskId.split('-')[0].toUpperCase()}
          </Typography>
          <Chip
            label={taskDetail.status.replace('_', ' ').toUpperCase()}
            color={isCompleted ? 'success' : isStopped || taskDetail.status === 'failed' ? 'error' : isPaused ? 'info' : 'warning'}
            size="small"
            sx={{ fontWeight: '700', borderRadius: '6px' }}
          />
        </Stack>
        <Typography variant="body1" color="text.secondary" sx={{ fontFamily: 'monospace', fontSize: '0.9rem' }}>
          {taskDetail.url}
        </Typography>
        <Typography variant="caption" color="text.disabled" sx={{ mt: 0.5, display: 'block' }}>
          Started At: {new Date(taskDetail.created_at || '').toLocaleString()}
        </Typography>
      </Box>

      <Stack component="div" direction="row" spacing={2}>
        {(isCompleted || isStopped) && (
          <>
            <Button
              variant="contained"
              color="primary"
              startIcon={<LaunchIcon />}
              onClick={handleOpenReport}
              sx={{ fontWeight: '700', borderRadius: '8px', px: 3, py: 1 }}
            >
              Allure Compliance Report
            </Button>
            <Button
              variant="outlined"
              color="primary"
              startIcon={<FileDownloadIcon />}
              onClick={handleExportReport}
              sx={{ fontWeight: '700', borderRadius: '8px', px: 3, py: 1 }}
            >
              Export Report (ZIP)
            </Button>
          </>
        )}

        {/* Active Controls */}
        {isRunning && (
          <>
            <Button
              variant="outlined"
              color="warning"
              startIcon={<PauseIcon />}
              onClick={handlePause}
              disabled={actionLoading}
              sx={{ fontWeight: '700', borderRadius: '8px' }}
            >
              Pause Audit
            </Button>
            <Button
              variant="contained"
              color="error"
              startIcon={<StopIcon />}
              onClick={handleStop}
              disabled={actionLoading}
              sx={{ fontWeight: '700', borderRadius: '8px' }}
            >
              Stop Audit
            </Button>
          </>
        )}

        {isPaused && (
          <>
            <Button
              variant="contained"
              color="success"
              startIcon={<PlayArrowIcon />}
              onClick={handleResume}
              disabled={actionLoading}
              sx={{ fontWeight: '700', borderRadius: '8px', color: '#ffffff' }}
            >
              Resume Audit
            </Button>
            <Button
              variant="contained"
              color="error"
              startIcon={<StopIcon />}
              onClick={handleStop}
              disabled={actionLoading}
              sx={{ fontWeight: '700', borderRadius: '8px' }}
            >
              Stop Audit
            </Button>
          </>
        )}
      </Stack>
    </Stack>
  );
};
