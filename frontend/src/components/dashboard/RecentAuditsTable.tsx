import { Box, TableRow, TableCell, IconButton, Typography, Tooltip, Button } from '@mui/material';
import { alpha } from '@mui/material/styles';
import LaunchIcon from '@mui/icons-material/Launch';
import PauseIcon from '@mui/icons-material/Pause';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import StopIcon from '@mui/icons-material/Stop';
import DeleteIcon from '@mui/icons-material/Delete';
import ArrowForwardIcon from '@mui/icons-material/ArrowForward';
import { StatusBadge } from '../common/badge';
import { DataTable, type ColumnDefinition } from '../common/table';
import type { DashboardStats as StatsType } from '../../model/dashboard.model';
import { useNavigate, useParams } from '@tanstack/react-router';
import { auditService } from '../../service/auditService';

interface RecentAuditsTableProps {
  stats: StatsType | null;
  loading?: boolean;
  onRefresh?: () => void;
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

export const RecentAuditsTable: React.FC<RecentAuditsTableProps> = ({ stats, loading = false, onRefresh }) => {
  const recentAudits = (stats?.recent_audits || []).slice(0, 5);
  const navigate = useNavigate();
  const { orgId } = useParams({ strict: false }) as any;

  const handleAuditClick = (taskId: string) => {
    navigate({ to: `/org/${orgId}/audits/${taskId}` });
  };

  const handlePause = async (e: React.MouseEvent, taskId: string) => {
    e.stopPropagation();
    try {
      await auditService.pauseAudit(taskId);
      if (onRefresh) onRefresh();
    } catch (err) {
      console.error('Failed to pause audit:', err);
    }
  };

  const handleResume = async (e: React.MouseEvent, taskId: string) => {
    e.stopPropagation();
    try {
      await auditService.resumeAudit(taskId);
      if (onRefresh) onRefresh();
    } catch (err) {
      console.error('Failed to resume audit:', err);
    }
  };

  const handleStop = async (e: React.MouseEvent, taskId: string) => {
    e.stopPropagation();
    if (window.confirm('Are you sure you want to stop this audit scan?')) {
      try {
        await auditService.stopAudit(taskId);
        if (onRefresh) onRefresh();
      } catch (err) {
        console.error('Failed to stop audit:', err);
      }
    }
  };

  const handleDelete = async (e: React.MouseEvent, taskId: string) => {
    e.stopPropagation();
    if (window.confirm('Are you sure you want to delete this audit session and all its data? This cannot be undone.')) {
      try {
        await auditService.deleteAudit(taskId);
        if (onRefresh) onRefresh();
      } catch (err) {
        console.error('Failed to delete audit:', err);
      }
    }
  };

  const columns: ColumnDefinition<any>[] = [
    { id: 'project_name', label: 'Project Name', sortable: false },
    { id: 'url', label: 'URL', sortable: false },
    { id: 'timestamp', label: 'Date', sortable: false },
    { id: 'accessibility_score', label: 'Score', sortable: false },
    { id: 'status', label: 'Status', sortable: false },
    { id: 'actions', label: 'Action', align: 'right', sortable: false }
  ];

  const renderRow = (run: any) => {
    const isCompleted = run.status.toLowerCase() === 'completed';
    const isPaused = run.status.toLowerCase() === 'paused';
    const isRunning = run.status.toLowerCase() === 'in_progress' || run.status.toLowerCase() === 'crawling' || run.status.toLowerCase() === 'auditing';
    const projName = run.project_name || getProjectNameFromUrl(run.url);
    const dateFormatted = new Date(run.timestamp).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });

    return (
      <TableRow 
        key={run.task_id} 
        hover 
        onClick={() => handleAuditClick(run.task_id)}
        sx={{ cursor: 'pointer' }}
      >
        <TableCell sx={{ fontWeight: '700', color: 'text.primary', py: 2 }}>{projName}</TableCell>
        <TableCell sx={{ color: 'text.secondary', fontFamily: 'monospace', fontSize: '0.8rem', py: 2 }}>{run.url}</TableCell>
        <TableCell sx={{ color: 'text.secondary', py: 2 }}>{dateFormatted}</TableCell>
        <TableCell sx={{ py: 2 }}>
          {run.status.toLowerCase() === 'completed' || run.status.toLowerCase() === 'in_progress' || run.status.toLowerCase() === 'crawling' || run.status.toLowerCase() === 'auditing' || run.status.toLowerCase() === 'paused' || run.status.toLowerCase() === 'stopped' ? (
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Box sx={{
                width: 32,
                height: 6,
                borderRadius: 3,
                bgcolor: run.accessibility_score >= 80 ? 'success.main' : run.accessibility_score >= 70 ? 'warning.main' : 'error.main'
              }} />
              <Typography sx={{ fontWeight: '700', color: 'text.primary', fontSize: '0.875rem' }}>{run.accessibility_score}</Typography>
            </Box>
          ) : (
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Box sx={{ width: 32, height: 6, borderRadius: 3, bgcolor: 'divider' }} />
              <Typography sx={{ fontWeight: '700', color: 'text.secondary', fontSize: '0.875rem' }}>N/A</Typography>
            </Box>
          )}
        </TableCell>
        <TableCell sx={{ py: 2 }}>
          <StatusBadge
            label={run.status === 'in_progress' ? 'Running...' : run.status === 'completed' ? 'Completed' : run.status}
            status={run.status}
            type="task"
          />
        </TableCell>
        <TableCell align="right" sx={{ py: 1 }} onClick={(e) => e.stopPropagation()}>
          <Box sx={{ display: 'flex', justifyContent: 'flex-end', gap: 0.5 }}>
            {isCompleted && (
              <Tooltip title="View Report">
                <IconButton
                  size="small"
                  onClick={() => handleAuditClick(run.task_id)}
                  sx={{ color: 'text.secondary', '&:hover': { color: 'primary.main' } }}
                >
                  <LaunchIcon fontSize="small" />
                </IconButton>
              </Tooltip>
            )}
            {isRunning && (
              <>
                <Tooltip title="Pause Audit">
                  <IconButton size="small" onClick={(e) => handlePause(e, run.task_id)} sx={{ color: 'warning.main' }}>
                    <PauseIcon fontSize="small" />
                  </IconButton>
                </Tooltip>
                <Tooltip title="Stop Audit">
                  <IconButton size="small" onClick={(e) => handleStop(e, run.task_id)} sx={{ color: 'error.main' }}>
                    <StopIcon fontSize="small" />
                  </IconButton>
                </Tooltip>
              </>
            )}
            {isPaused && (
              <>
                <Tooltip title="Resume Audit">
                  <IconButton size="small" onClick={(e) => handleResume(e, run.task_id)} sx={{ color: 'success.main' }}>
                    <PlayArrowIcon fontSize="small" />
                  </IconButton>
                </Tooltip>
                <Tooltip title="Stop Audit">
                  <IconButton size="small" onClick={(e) => handleStop(e, run.task_id)} sx={{ color: 'error.main' }}>
                    <StopIcon fontSize="small" />
                  </IconButton>
                </Tooltip>
              </>
            )}
            <Tooltip title="Delete Session">
              <IconButton
                size="small"
                onClick={(e) => handleDelete(e, run.task_id)}
                sx={{ color: 'text.disabled', '&:hover': { color: 'error.main' } }}
              >
                <DeleteIcon fontSize="small" />
              </IconButton>
            </Tooltip>
          </Box>
        </TableCell>
      </TableRow>
    );
  };

  return (
    <Box>
      <DataTable
        searchTerm=""
        loading={loading}
        totalCount={recentAudits.length}
        page={0}
        rowsPerPage={5}
        onPageChange={() => {}}
        onRowsPerPageChange={() => {}}
        columns={columns}
        data={recentAudits}
        renderRow={renderRow}
        hidePagination={true}
        headerActions={
          <Box sx={{ 
            display: 'flex', 
            justifyContent: 'space-between', 
            alignItems: 'center', 
            width: '100%',
            flexWrap: 'wrap',
            gap: 2
          }}>
            <Box>
              <Typography variant="h6" sx={{ color: '#16191f', fontWeight: '800', fontFamily: 'Outfit', fontSize: '1rem', lineHeight: 1.2 }}>
                Recent Audits
              </Typography>
              <Typography variant="caption" sx={{ color: '#545b64', fontWeight: '500', display: 'block', mt: 0.5 }}>
                Displaying only the last 5 audit scans.
              </Typography>
            </Box>
            <Button
              variant="outlined"
              size="small"
              onClick={() => navigate({ to: `/org/${orgId}/audits` })}
              endIcon={<ArrowForwardIcon fontSize="small" />}
              sx={{ 
                textTransform: 'none', 
                fontWeight: '700', 
                borderRadius: '8px',
                borderColor: 'divider',
                color: 'primary.main',
                '&:hover': {
                  bgcolor: (theme) => alpha(theme.palette.primary.main, 0.04),
                  borderColor: 'primary.main'
                }
              }}
            >
              View Full History
            </Button>
          </Box>
        }
      />
    </Box>
  );
};
