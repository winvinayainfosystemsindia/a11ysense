import React, { useState } from 'react';
import {
  Box,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  Button,
  IconButton,
  Tooltip,
  TextField,
  InputAdornment,
  Stack,
  Card,
  CircularProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogContentText,
  DialogActions,
  useTheme,
} from '@mui/material';
import { alpha } from '@mui/material/styles';
import SearchIcon from '@mui/icons-material/Search';
import VisibilityIcon from '@mui/icons-material/Visibility';
import FileDownloadIcon from '@mui/icons-material/FileDownload';
import DescriptionIcon from '@mui/icons-material/Description';
import DeleteIcon from '@mui/icons-material/Delete';
import AddIcon from '@mui/icons-material/Add';
import CalculateOutlinedIcon from '@mui/icons-material/CalculateOutlined';
import LanguageIcon from '@mui/icons-material/Language';

import type { SavedEstimateRecord } from '../../service/estimationService';
import { estimationService } from '../../service/estimationService';

interface EstimatesListTableProps {
  estimates: SavedEstimateRecord[];
  loading: boolean;
  onViewDetails: (estimateId: string) => void;
  onOpenCreate: () => void;
  onRefresh: () => void;
}

export const EstimatesListTable: React.FC<EstimatesListTableProps> = ({
  estimates,
  loading,
  onViewDetails,
  onOpenCreate,
  onRefresh,
}) => {
  const theme = useTheme();
  const [searchTerm, setSearchTerm] = useState('');
  const [downloadingId, setDownloadingId] = useState<string | null>(null);
  const [deleteConfirmId, setDeleteConfirmId] = useState<string | null>(null);
  const [deleting, setDeleting] = useState(false);

  const filtered = estimates.filter((item) => {
    if (!searchTerm) return true;
    const term = searchTerm.toLowerCase();
    return (
      item.title.toLowerCase().includes(term) ||
      item.base_url.toLowerCase().includes(term)
    );
  });

  const handleDownloadExcel = async (e: React.MouseEvent, estimate: SavedEstimateRecord) => {
    e.stopPropagation();
    setDownloadingId(`excel-${estimate.id}`);
    try {
      // If estimate has full pages & summary, use them; otherwise fetch details
      let full = estimate;
      if (!estimate.pages || !estimate.summary) {
        full = await estimationService.get(estimate.id);
      }
      await estimationService.downloadQuotationExcel({
        summary: full.summary!,
        pages: full.pages!,
      });
    } catch (err) {
      console.error('Failed to export Excel quote:', err);
    } finally {
      setDownloadingId(null);
    }
  };

  const handleDownloadPdf = async (e: React.MouseEvent, estimate: SavedEstimateRecord) => {
    e.stopPropagation();
    setDownloadingId(`pdf-${estimate.id}`);
    try {
      let full = estimate;
      if (!estimate.pages || !estimate.summary) {
        full = await estimationService.get(estimate.id);
      }
      await estimationService.downloadQuotationPdf({
        summary: full.summary!,
        pages: full.pages!,
      });
    } catch (err) {
      console.error('Failed to export PDF proposal:', err);
    } finally {
      setDownloadingId(null);
    }
  };

  const handleDelete = async () => {
    if (!deleteConfirmId) return;
    setDeleting(true);
    try {
      await estimationService.delete(deleteConfirmId);
      setDeleteConfirmId(null);
      onRefresh();
    } catch (err) {
      console.error('Failed to delete estimation:', err);
    } finally {
      setDeleting(false);
    }
  };

  const formatDate = (dateStr?: string) => {
    if (!dateStr) return '—';
    try {
      const d = new Date(dateStr);
      return d.toLocaleDateString(undefined, {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
      });
    } catch {
      return dateStr;
    }
  };

  if (loading && estimates.length === 0) {
    return (
      <Card variant="outlined" sx={{ p: 6, textAlign: 'center', borderRadius: 3 }}>
        <CircularProgress size={40} sx={{ mb: 2 }} />
        <Typography variant="body1" color="text.secondary">
          Loading audit estimations...
        </Typography>
      </Card>
    );
  }

  if (estimates.length === 0) {
    return (
      <Card
        variant="outlined"
        sx={{
          p: { xs: 4, md: 8 },
          textAlign: 'center',
          borderRadius: 4,
          bgcolor: alpha(theme.palette.background.default, 0.4),
        }}
      >
        <Box
          sx={{
            width: 72,
            height: 72,
            borderRadius: '50%',
            bgcolor: alpha(theme.palette.primary.main, 0.1),
            color: theme.palette.primary.main,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            mx: 'auto',
            mb: 2.5,
          }}
        >
          <CalculateOutlinedIcon sx={{ fontSize: 38 }} />
        </Box>
        <Typography variant="h5" sx={{ fontWeight: 800, mb: 1 }}>
          No Estimations Created Yet
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ maxWidth: 480, mx: 'auto', mb: 3 }}>
          Calculate commercial accessibility audit proposals, inspect web DOM complexity tiers, and generate executive Excel and PDF quotations.
        </Typography>
        <Button
          variant="contained"
          color="primary"
          size="large"
          startIcon={<AddIcon />}
          onClick={onOpenCreate}
          sx={{ fontWeight: 700, borderRadius: 2.5, px: 3, py: 1.2 }}
        >
          Create First Estimate
        </Button>
      </Card>
    );
  }

  return (
    <Box>
      {/* Search and stats bar */}
      <Stack
        component="div"
        direction={{ xs: 'column', sm: 'row' }}
        spacing={2}
        sx={{ justifyContent: 'space-between', alignItems: { xs: 'flex-start', sm: 'center' }, mb: 2.5 }}
      >
        <TextField
          size="small"
          placeholder="Search estimations by title or URL..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          slotProps={{
            input: {
              startAdornment: (
                <InputAdornment position="start">
                  <SearchIcon fontSize="small" color="action" />
                </InputAdornment>
              ),
            },
          }}
          sx={{ width: { xs: '100%', sm: 320 }, bgcolor: 'background.paper' }}
        />

        <Typography variant="body2" color="text.secondary">
          Showing <strong>{filtered.length}</strong> of <strong>{estimates.length}</strong> estimations
        </Typography>
      </Stack>

      {/* Main Table */}
      <TableContainer
        component={Paper}
        variant="outlined"
        sx={{
          borderRadius: 3,
          boxShadow: 'none',
          overflow: 'hidden',
        }}
      >
        <Table>
          <TableHead>
            <TableRow sx={{ bgcolor: alpha(theme.palette.text.primary, 0.03) }}>
              <TableCell sx={{ fontWeight: 800, py: 2 }}>Estimate Details</TableCell>
              <TableCell sx={{ fontWeight: 800, py: 2 }}>Created</TableCell>
              <TableCell sx={{ fontWeight: 800, py: 2, textAlign: 'center' }}>Pages</TableCell>
              <TableCell sx={{ fontWeight: 800, py: 2 }}>Tier Distribution</TableCell>
              <TableCell sx={{ fontWeight: 800, py: 2, textAlign: 'right' }}>Effort</TableCell>
              <TableCell sx={{ fontWeight: 800, py: 2, textAlign: 'right' }}>Total Quote</TableCell>
              <TableCell sx={{ fontWeight: 800, py: 2, textAlign: 'center' }}>Status</TableCell>
              <TableCell sx={{ fontWeight: 800, py: 2, textAlign: 'right' }}>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {filtered.map((item) => (
              <TableRow
                key={item.id}
                hover
                onClick={() => onViewDetails(item.id)}
                sx={{
                  cursor: 'pointer',
                  '&:last-child td, &:last-child th': { border: 0 },
                }}
              >
                {/* Title & URL */}
                <TableCell sx={{ py: 2, maxWidth: 320 }}>
                  <Typography variant="subtitle2" sx={{ fontWeight: 700, mb: 0.5 }}>
                    {item.title}
                  </Typography>
                  <Stack component="div" direction="row" spacing={0.5} sx={{ alignItems: 'center' }}>
                    <LanguageIcon sx={{ fontSize: 14, color: 'text.secondary' }} />
                    <Typography
                      variant="caption"
                      color="text.secondary"
                      sx={{
                        maxWidth: 260,
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                        whiteSpace: 'nowrap',
                      }}
                    >
                      {item.base_url}
                    </Typography>
                  </Stack>
                </TableCell>

                {/* Date */}
                <TableCell sx={{ py: 2, color: 'text.secondary', fontSize: '0.875rem' }}>
                  {formatDate(item.created_at)}
                </TableCell>

                {/* Pages */}
                <TableCell sx={{ py: 2, textAlign: 'center' }}>
                  <Typography variant="body2" sx={{ fontWeight: 800 }}>
                    {item.total_pages}
                  </Typography>
                </TableCell>

                {/* Complexity Breakdown */}
                <TableCell sx={{ py: 2 }}>
                  <Stack component="div" direction="row" spacing={0.75} sx={{ flexWrap: 'wrap', gap: 0.5 }}>
                    {item.simple_pages > 0 && (
                      <Chip
                        label={`${item.simple_pages} Simple`}
                        size="small"
                        sx={{
                          fontWeight: 700,
                          fontSize: '0.72rem',
                          height: 22,
                          bgcolor: alpha(theme.palette.success.main, 0.1),
                          color: theme.palette.success.dark,
                        }}
                      />
                    )}
                    {item.medium_pages > 0 && (
                      <Chip
                        label={`${item.medium_pages} Medium`}
                        size="small"
                        sx={{
                          fontWeight: 700,
                          fontSize: '0.72rem',
                          height: 22,
                          bgcolor: alpha(theme.palette.info.main, 0.1),
                          color: theme.palette.info.dark,
                        }}
                      />
                    )}
                    {item.complex_pages > 0 && (
                      <Chip
                        label={`${item.complex_pages} Complex`}
                        size="small"
                        sx={{
                          fontWeight: 700,
                          fontSize: '0.72rem',
                          height: 22,
                          bgcolor: alpha(theme.palette.warning.main, 0.12),
                          color: theme.palette.warning.dark,
                        }}
                      />
                    )}
                  </Stack>
                </TableCell>

                {/* Effort */}
                <TableCell sx={{ py: 2, textAlign: 'right' }}>
                  <Typography variant="body2" sx={{ fontWeight: 700 }}>
                    {item.total_manual_hours} hrs
                  </Typography>
                </TableCell>

                {/* Total Quote */}
                <TableCell sx={{ py: 2, textAlign: 'right' }}>
                  <Typography variant="subtitle2" color="primary" sx={{ fontWeight: 800 }}>
                    ${Number(item.total_quote).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                  </Typography>
                </TableCell>

                {/* Status */}
                <TableCell sx={{ py: 2, textAlign: 'center' }}>
                  <Chip
                    label={item.status || 'completed'}
                    size="small"
                    color={item.status === 'failed' ? 'error' : 'success'}
                    variant="outlined"
                    sx={{ textTransform: 'capitalize', fontWeight: 700, fontSize: '0.72rem', height: 22 }}
                  />
                </TableCell>

                {/* Actions */}
                <TableCell sx={{ py: 2, textAlign: 'right' }} onClick={(e) => e.stopPropagation()}>
                  <Stack component="div" direction="row" spacing={0.5} sx={{ justifyContent: 'flex-end' }}>
                    <Tooltip title="View Detailed Breakdown">
                      <IconButton
                        size="small"
                        color="primary"
                        onClick={() => onViewDetails(item.id)}
                      >
                        <VisibilityIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>

                    <Tooltip title="Download Excel Quote">
                      <IconButton
                        size="small"
                        color="success"
                        onClick={(e) => handleDownloadExcel(e, item)}
                        disabled={downloadingId === `excel-${item.id}`}
                      >
                        {downloadingId === `excel-${item.id}` ? (
                          <CircularProgress size={16} color="inherit" />
                        ) : (
                          <FileDownloadIcon fontSize="small" />
                        )}
                      </IconButton>
                    </Tooltip>

                    <Tooltip title="Download PDF Proposal">
                      <IconButton
                        size="small"
                        color="info"
                        onClick={(e) => handleDownloadPdf(e, item)}
                        disabled={downloadingId === `pdf-${item.id}`}
                      >
                        {downloadingId === `pdf-${item.id}` ? (
                          <CircularProgress size={16} color="inherit" />
                        ) : (
                          <DescriptionIcon fontSize="small" />
                        )}
                      </IconButton>
                    </Tooltip>

                    <Tooltip title="Delete Estimation">
                      <IconButton
                        size="small"
                        color="error"
                        onClick={() => setDeleteConfirmId(item.id)}
                      >
                        <DeleteIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                  </Stack>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Delete Confirmation Dialog */}
      <Dialog
        open={Boolean(deleteConfirmId)}
        onClose={() => setDeleteConfirmId(null)}
        maxWidth="xs"
        fullWidth
      >
        <DialogTitle sx={{ fontWeight: 800 }}>Delete Estimation?</DialogTitle>
        <DialogContent>
          <DialogContentText>
            Are you sure you want to delete this saved audit estimation? This action cannot be undone.
          </DialogContentText>
        </DialogContent>
        <DialogActions sx={{ px: 3, pb: 2.5 }}>
          <Button onClick={() => setDeleteConfirmId(null)} color="inherit" disabled={deleting}>
            Cancel
          </Button>
          <Button onClick={handleDelete} color="error" variant="contained" disabled={deleting}>
            {deleting ? 'Deleting...' : 'Delete'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};
