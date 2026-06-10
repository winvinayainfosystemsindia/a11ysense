import React, { useState } from 'react';
import {
  Typography,
  Chip,
  Box,
  CircularProgress,
  useTheme,
  IconButton,
  Tooltip,
  TableRow,
  TableCell
} from '@mui/material';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import PauseIcon from '@mui/icons-material/Pause';
import StopIcon from '@mui/icons-material/Stop';
import DeleteIcon from '@mui/icons-material/Delete';
import { useNavigate, useParams } from '@tanstack/react-router';
import { auditService } from '../../service/auditService';
import type { AuditSessionInfo } from '../../service/auditService';
import DataTable from '../common/table/DataTable';
import type { ColumnDefinition } from '../common/table/DataTable';
import ConfirmationDialog from '../common/dialogbox/ConfirmationDialog';

interface AuditsTableProps {
  audits: AuditSessionInfo[];
  isLoading: boolean;
  onRefresh?: () => void;
}

type DialogAction = 'stop' | 'delete' | null;

const getStatusColor = (status: string) => {
  switch (status.toLowerCase()) {
    case 'completed': return 'success';
    case 'failed': return 'error';
    case 'stopped': return 'error';
    case 'paused': return 'info';
    case 'in_progress':
    case 'crawling':
    case 'auditing':
    case 'pending':
    default: return 'warning';
  }
};

const COLUMNS: ColumnDefinition<AuditSessionInfo>[] = [
  { id: 'url', label: 'Target URL', sortable: true, align: 'left' },
  { id: 'project_name', label: 'Project', sortable: true, align: 'left' },
  { id: 'timestamp', label: 'Started At', sortable: true, align: 'left' },
  { id: 'status', label: 'Status', sortable: true, align: 'left' },
  { id: 'accessibility_score', label: 'Score', sortable: true, align: 'right' },
  { id: 'total_violations', label: 'Violations', sortable: false, align: 'right' },
  { id: 'actions', label: 'Actions', sortable: false, align: 'right' },
];

const AuditsTable: React.FC<AuditsTableProps> = ({ audits, isLoading, onRefresh }) => {
  const theme = useTheme();
  const navigate = useNavigate();
  const { orgId } = useParams({ strict: false }) as any;

  // Search state
  const [searchTerm, setSearchTerm] = useState('');

  // Pagination state
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);

  // Sort state
  const [order, setOrder] = useState<'asc' | 'desc'>('desc');
  const [orderBy, setOrderBy] = useState<keyof AuditSessionInfo>('timestamp');

  // Confirmation dialog state
  const [dialogOpen, setDialogOpen] = useState(false);
  const [dialogAction, setDialogAction] = useState<DialogAction>(null);
  const [targetTaskId, setTargetTaskId] = useState<string | null>(null);
  const [actionLoading, setActionLoading] = useState(false);

  const handleRowClick = (taskId: string) => {
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

  const openStopDialog = (e: React.MouseEvent, taskId: string) => {
    e.stopPropagation();
    setDialogAction('stop');
    setTargetTaskId(taskId);
    setDialogOpen(true);
  };

  const openDeleteDialog = (e: React.MouseEvent, taskId: string) => {
    e.stopPropagation();
    setDialogAction('delete');
    setTargetTaskId(taskId);
    setDialogOpen(true);
  };

  const handleDialogClose = () => {
    if (actionLoading) return;
    setDialogOpen(false);
    setDialogAction(null);
    setTargetTaskId(null);
  };

  const handleDialogConfirm = async () => {
    if (!targetTaskId || !dialogAction) return;
    setActionLoading(true);
    try {
      if (dialogAction === 'stop') {
        await auditService.stopAudit(targetTaskId);
      } else if (dialogAction === 'delete') {
        await auditService.deleteAudit(targetTaskId);
      }
      if (onRefresh) onRefresh();
    } catch (err) {
      console.error(`Failed to ${dialogAction} audit:`, err);
    } finally {
      setActionLoading(false);
      setDialogOpen(false);
      setDialogAction(null);
      setTargetTaskId(null);
    }
  };

  // Sort handling
  const handleSortRequest = (property: keyof AuditSessionInfo) => {
    const isAsc = orderBy === property && order === 'asc';
    setOrder(isAsc ? 'desc' : 'asc');
    setOrderBy(property);
    setPage(0);
  };

  // Filter audits by search term
  const filteredAudits = searchTerm.trim()
    ? audits.filter(
        (a) =>
          a.url.toLowerCase().includes(searchTerm.toLowerCase()) ||
          (a.project_name || '').toLowerCase().includes(searchTerm.toLowerCase())
      )
    : audits;

  // Sort the audits
  const sortedAudits = [...filteredAudits].sort((a, b) => {
    const aVal = a[orderBy];
    const bVal = b[orderBy];
    if (aVal === undefined || bVal === undefined) return 0;
    if (typeof aVal === 'number' && typeof bVal === 'number') {
      return order === 'asc' ? aVal - bVal : bVal - aVal;
    }
    const aStr = String(aVal);
    const bStr = String(bVal);
    return order === 'asc' ? aStr.localeCompare(bStr) : bStr.localeCompare(aStr);
  });

  // Paginate
  const paginatedAudits = sortedAudits.slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage);
  const totalFilteredCount = filteredAudits.length;

  const dialogConfig = {
    stop: {
      title: 'Stop Audit Scan',
      message: 'Are you sure you want to stop this audit scan? Progress so far will be saved but the scan will not complete.',
      confirmLabel: 'Stop Scan',
      severity: 'warning' as const,
    },
    delete: {
      title: 'Delete Audit Session',
      message: 'Are you sure you want to permanently delete this audit session and all its data? This action cannot be undone.',
      confirmLabel: 'Delete',
      severity: 'error' as const,
    },
  };

  const activeDialogConfig = dialogAction ? dialogConfig[dialogAction] : null;

  const renderRow = (audit: AuditSessionInfo) => (
    <TableRow
      key={audit.task_id}
      onClick={() => handleRowClick(audit.task_id)}
      sx={{
        cursor: 'pointer',
        '&:last-child td, &:last-child th': { border: 0 },
        '&:hover': { bgcolor: `${theme.palette.primary.main}0d` },
        transition: 'background-color 0.2s',
      }}
    >
      {/* Target URL */}
      <TableCell>
        <Typography variant="subtitle2" sx={{ fontWeight: 600, maxWidth: 260, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
          {audit.url}
        </Typography>
        <Typography variant="caption" color="text.secondary">
          ID: {audit.task_id.split('-')[0]}...
        </Typography>
      </TableCell>

      {/* Project */}
      <TableCell>
        <Typography variant="body2" color="text.secondary">
          {audit.project_name}
        </Typography>
      </TableCell>

      {/* Started At */}
      <TableCell>
        <Typography variant="body2">
          {new Date(audit.timestamp).toLocaleString()}
        </Typography>
      </TableCell>

      {/* Status */}
      <TableCell>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          {(audit.status === 'in_progress' || audit.status === 'crawling' || audit.status === 'auditing' || audit.status === 'pending') && (
            <CircularProgress size={12} thickness={5} sx={{ color: theme.palette.warning.main }} />
          )}
          <Chip
            label={audit.status.replace(/_/g, ' ').toUpperCase()}
            size="small"
            color={getStatusColor(audit.status) as any}
            sx={{ fontWeight: 700, fontSize: '0.7rem' }}
          />
        </Box>
      </TableCell>

      {/* Score */}
      <TableCell align="right">
        {audit.status === 'completed' ? (
          <Typography
            variant="body2"
            sx={{
              fontWeight: 700,
              color:
                audit.accessibility_score >= 90
                  ? 'success.main'
                  : audit.accessibility_score >= 70
                  ? 'warning.main'
                  : 'error.main',
            }}
          >
            {audit.accessibility_score.toFixed(1)}
          </Typography>
        ) : (
          <Typography variant="body2" color="text.disabled">-</Typography>
        )}
      </TableCell>

      {/* Violations */}
      <TableCell align="right">
        {audit.status === 'completed' ? (
          <Chip
            label={`${audit.total_violations} issues`}
            size="small"
            variant="outlined"
            color={audit.total_violations === 0 ? 'success' : audit.total_violations < 10 ? 'warning' : 'error'}
            sx={{ fontWeight: 600, fontSize: '0.75rem' }}
          />
        ) : (
          <Typography variant="body2" color="text.disabled">-</Typography>
        )}
      </TableCell>

      {/* Actions */}
      <TableCell align="right" onClick={(e) => e.stopPropagation()}>
        <Box sx={{ display: 'flex', justifyContent: 'flex-end', gap: 0.5 }}>
          {(audit.status === 'in_progress' || audit.status === 'crawling' || audit.status === 'auditing') && (
            <Tooltip title="Pause Audit">
              <IconButton size="small" onClick={(e) => handlePause(e, audit.task_id)} sx={{ color: 'warning.main' }}>
                <PauseIcon fontSize="small" />
              </IconButton>
            </Tooltip>
          )}
          {audit.status === 'paused' && (
            <Tooltip title="Resume Audit">
              <IconButton size="small" onClick={(e) => handleResume(e, audit.task_id)} sx={{ color: 'success.main' }}>
                <PlayArrowIcon fontSize="small" />
              </IconButton>
            </Tooltip>
          )}
          {(audit.status === 'in_progress' || audit.status === 'crawling' || audit.status === 'auditing' || audit.status === 'paused') && (
            <Tooltip title="Stop Audit">
              <IconButton size="small" onClick={(e) => openStopDialog(e, audit.task_id)} sx={{ color: 'error.main' }}>
                <StopIcon fontSize="small" />
              </IconButton>
            </Tooltip>
          )}
          <Tooltip title="Delete Session">
            <IconButton
              size="small"
              onClick={(e) => openDeleteDialog(e, audit.task_id)}
              sx={{ color: 'text.disabled', '&:hover': { color: 'error.main' } }}
            >
              <DeleteIcon fontSize="small" />
            </IconButton>
          </Tooltip>
        </Box>
      </TableCell>
    </TableRow>
  );

  return (
    <>
      <DataTable<AuditSessionInfo>
        columns={COLUMNS}
        data={paginatedAudits}
        totalCount={totalFilteredCount}
        page={page}
        rowsPerPage={rowsPerPage}
        onPageChange={(_e, newPage) => setPage(newPage)}
        onRowsPerPageChange={(newRowsPerPage) => {
          setRowsPerPage(newRowsPerPage);
          setPage(0);
        }}
        orderBy={orderBy}
        order={order}
        onSortRequest={handleSortRequest}
        loading={isLoading}
        onRefresh={onRefresh}
        emptyMessage="No audits found. Start an audit to see history here!"
        searchTerm={searchTerm}
        onSearchChange={(val) => { setSearchTerm(val); setPage(0); }}
        searchPlaceholder="Search by URL or project..."
        renderRow={renderRow}
      />

      {activeDialogConfig && (
        <ConfirmationDialog
          open={dialogOpen}
          onClose={handleDialogClose}
          onConfirm={handleDialogConfirm}
          title={activeDialogConfig.title}
          message={activeDialogConfig.message}
          confirmLabel={activeDialogConfig.confirmLabel}
          severity={activeDialogConfig.severity}
          loading={actionLoading}
        />
      )}
    </>
  );
};

export default AuditsTable;
