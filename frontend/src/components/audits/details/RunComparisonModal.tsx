import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Box,
  Typography,
  Stack,
  Tabs,
  Tab,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  CircularProgress,
  IconButton
} from '@mui/material';
import CloseIcon from '@mui/icons-material/Close';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import NewReleasesIcon from '@mui/icons-material/NewReleases';
import BugReportIcon from '@mui/icons-material/BugReport';
import ArrowForwardIcon from '@mui/icons-material/ArrowForward';

import { regressionService } from '../../../service/regressionService';
import type { RunComparison } from '../../../model/regression.model';

interface Props {
  open: boolean;
  onClose: () => void;
  currentTaskId: string;
  previousTaskId: string | null;
}

export const RunComparisonModal: React.FC<Props> = ({
  open,
  onClose,
  currentTaskId,
  previousTaskId
}) => {
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState<RunComparison | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [tabIndex, setTabIndex] = useState(0);

  useEffect(() => {
    if (!open) return;

    let isMounted = true;
    const fetchComparison = async () => {
      try {
        setLoading(true);
        setError(null);
        let runA = previousTaskId;
        if (!runA) {
          const reg = await regressionService.getRegressionSummary(currentTaskId);
          if (reg && reg.previous_run_number) {
            runA = `run-${reg.previous_run_number}`;
          }
        }
        const res = await regressionService.compareAudits(runA || currentTaskId, currentTaskId);
        if (isMounted) setData(res);
      } catch (err: any) {
        if (isMounted) setError(err?.userMessage || 'Failed to compare audit runs.');
      } finally {
        if (isMounted) setLoading(false);
      }
    };
    fetchComparison();
    return () => {
      isMounted = false;
    };
  }, [open, currentTaskId, previousTaskId]);

  return (
    <Dialog open={open} onClose={onClose} maxWidth="lg" fullWidth>
      <DialogTitle sx={{ m: 0, p: 2.5, bgcolor: '#0f172a', color: '#f8fafc', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography variant="h6" sx={{ fontWeight: 800 }}>
          Audit Run Comparison
        </Typography>
        <IconButton onClick={onClose} sx={{ color: '#94a3b8' }}>
          <CloseIcon />
        </IconButton>
      </DialogTitle>

      <DialogContent sx={{ p: 3, bgcolor: '#0b1120', minHeight: 450 }}>
        {loading ? (
          <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', py: 10 }}>
            <CircularProgress size={40} />
            <Typography variant="body2" sx={{ mt: 2, color: '#94a3b8' }}>Reconciling audit run differences...</Typography>
          </Box>
        ) : error || !data ? (
          <Box sx={{ py: 6, textAlign: 'center' }}>
            <Typography color="error" variant="body1">{error || 'No comparison data available.'}</Typography>
          </Box>
        ) : (
          <Box>
            {/* Run comparison summary header */}
            <Paper
              sx={{
                p: 2.5,
                mb: 3,
                bgcolor: '#1e293b',
                border: '1px solid #334155',
                borderRadius: 2
              }}
            >
              <Stack
                component="div"
                direction={{ xs: 'column', sm: 'row' }}
                spacing={2}
                sx={{
                  alignItems: 'center',
                  justifyContent: 'space-around'
                }}
              >
                {/* Run A */}
                <Box sx={{ textAlign: 'center' }}>
                  <Typography variant="caption" sx={{ color: '#94a3b8', textTransform: 'uppercase' }}>
                    Run #{data.run_a.run_number} (Previous)
                  </Typography>
                  <Typography variant="h5" sx={{ fontWeight: 800, color: '#f8fafc', mt: 0.5 }}>
                    {data.run_a.score}%
                  </Typography>
                  <Typography variant="caption" sx={{ color: '#64748b' }}>
                    {data.run_a.task_id}
                  </Typography>
                </Box>

                <Stack component="div" direction="column" sx={{ alignItems: 'center' }}>
                  <ArrowForwardIcon sx={{ color: '#64748b', fontSize: 28 }} />
                  <Chip
                    label={`${data.score_delta >= 0 ? '+' : ''}${data.score_delta}%`}
                    size="small"
                    sx={{
                      fontWeight: 800,
                      bgcolor: data.score_delta >= 0 ? 'rgba(34, 197, 94, 0.2)' : 'rgba(239, 68, 68, 0.2)',
                      color: data.score_delta >= 0 ? '#4ade80' : '#f87171',
                      mt: 0.5
                    }}
                  />
                </Stack>

                {/* Run B */}
                <Box sx={{ textAlign: 'center' }}>
                  <Typography variant="caption" sx={{ color: '#94a3b8', textTransform: 'uppercase' }}>
                    Run #{data.run_b.run_number} (Current)
                  </Typography>
                  <Typography variant="h5" sx={{ fontWeight: 800, color: '#f8fafc', mt: 0.5 }}>
                    {data.run_b.score}%
                  </Typography>
                  <Typography variant="caption" sx={{ color: '#64748b' }}>
                    {data.run_b.task_id}
                  </Typography>
                </Box>
              </Stack>
            </Paper>

            {/* Tabs for Differences */}
            <Box sx={{ borderBottom: 1, borderColor: '#334155', mb: 2 }}>
              <Tabs
                value={tabIndex}
                onChange={(_, val) => setTabIndex(val)}
                textColor="primary"
                indicatorColor="primary"
              >
                <Tab
                  icon={<CheckCircleIcon sx={{ fontSize: 18 }} />}
                  iconPosition="start"
                  label={`Fixed in Run #${data.run_b.run_number} (${data.fixed_in_b?.length || 0})`}
                  sx={{ fontWeight: 700, textTransform: 'none', color: '#94a3b8' }}
                />
                <Tab
                  icon={<NewReleasesIcon sx={{ fontSize: 18 }} />}
                  iconPosition="start"
                  label={`New Regressions (${data.new_in_b?.length || 0})`}
                  sx={{ fontWeight: 700, textTransform: 'none', color: '#94a3b8' }}
                />
                <Tab
                  icon={<BugReportIcon sx={{ fontSize: 18 }} />}
                  iconPosition="start"
                  label={`Common Open (${data.common_open?.length || 0})`}
                  sx={{ fontWeight: 700, textTransform: 'none', color: '#94a3b8' }}
                />
              </Tabs>
            </Box>

            {/* Tab Panels */}
            {tabIndex === 0 && (
              <DifferenceTable
                items={data.fixed_in_b || []}
                emptyMessage="No fixed defects between these two runs."
                statusBadge="Fixed"
                statusColor="success"
              />
            )}
            {tabIndex === 1 && (
              <DifferenceTable
                items={data.new_in_b || []}
                emptyMessage="No new regression defects detected in this run."
                statusBadge="New"
                statusColor="error"
              />
            )}
            {tabIndex === 2 && (
              <DifferenceTable
                items={data.common_open || []}
                emptyMessage="No common open defects."
                statusBadge="Open"
                statusColor="info"
              />
            )}
          </Box>
        )}
      </DialogContent>

      <DialogActions sx={{ p: 2, bgcolor: '#0f172a', borderTop: '1px solid #1e293b' }}>
        <Button onClick={onClose} variant="contained" color="primary">
          Close
        </Button>
      </DialogActions>
    </Dialog>
  );
};

interface DiffTableProps {
  items: any[];
  emptyMessage: string;
  statusBadge: string;
  statusColor: 'success' | 'error' | 'info';
}

const DifferenceTable: React.FC<DiffTableProps> = ({ items, emptyMessage, statusBadge, statusColor }) => {
  if (!items.length) {
    return (
      <Box sx={{ py: 6, textAlign: 'center' }}>
        <Typography variant="body2" sx={{ color: '#64748b' }}>{emptyMessage}</Typography>
      </Box>
    );
  }

  return (
    <TableContainer component={Paper} sx={{ bgcolor: '#0f172a', border: '1px solid #1e293b' }}>
      <Table size="small">
        <TableHead>
          <TableRow sx={{ bgcolor: '#1e293b' }}>
            <TableCell sx={{ color: '#94a3b8', fontWeight: 700 }}>Defect / Rule</TableCell>
            <TableCell sx={{ color: '#94a3b8', fontWeight: 700 }}>WCAG Criterion</TableCell>
            <TableCell sx={{ color: '#94a3b8', fontWeight: 700 }}>Severity</TableCell>
            <TableCell sx={{ color: '#94a3b8', fontWeight: 700 }}>Page URL</TableCell>
            <TableCell sx={{ color: '#94a3b8', fontWeight: 700 }}>Status</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {items.map((it, idx) => (
            <TableRow key={idx} hover sx={{ '&:last-child td, &:last-child th': { border: 0 } }}>
              <TableCell sx={{ color: '#f8fafc', fontWeight: 600 }}>
                {it.defect_code || it.rule_id || 'N/A'}
                <Typography variant="caption" sx={{ color: '#64748b', display: 'block' }}>
                  {it.testcase_name || it.description || ''}
                </Typography>
              </TableCell>
              <TableCell sx={{ color: '#cbd5e1' }}>{it.criteria || it.sc_code || 'N/A'}</TableCell>
              <TableCell>
                <Chip
                  label={it.severity || 'Moderate'}
                  size="small"
                  sx={{
                    fontWeight: 700,
                    fontSize: '0.7rem',
                    bgcolor:
                      it.severity === 'Critical'
                        ? 'rgba(239, 68, 68, 0.2)'
                        : it.severity === 'Serious'
                        ? 'rgba(245, 158, 11, 0.2)'
                        : 'rgba(59, 130, 246, 0.2)',
                    color:
                      it.severity === 'Critical'
                        ? '#f87171'
                        : it.severity === 'Serious'
                        ? '#fbbf24'
                        : '#60a5fa'
                  }}
                />
              </TableCell>
              <TableCell sx={{ color: '#94a3b8', maxWidth: 220, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                {it.page_url || '-'}
              </TableCell>
              <TableCell>
                <Chip label={statusBadge} size="small" color={statusColor} sx={{ fontWeight: 700 }} />
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  );
};
