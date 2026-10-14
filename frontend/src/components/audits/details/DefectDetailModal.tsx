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
  Chip,
  CircularProgress,
  IconButton,
  Divider,
  Paper,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  TextField,
  Alert
} from '@mui/material';
import CloseIcon from '@mui/icons-material/Close';
import HistoryIcon from '@mui/icons-material/History';
import BugReportIcon from '@mui/icons-material/BugReport';

import { regressionService } from '../../../service/regressionService';
import type { DefectDetail } from '../../../model/regression.model';

interface Props {
  open: boolean;
  onClose: () => void;
  defectId: string;
  onUpdated?: () => void;
}

export const DefectDetailModal: React.FC<Props> = ({
  open,
  onClose,
  defectId,
  onUpdated
}) => {
  const [defect, setDefect] = useState<DefectDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Status override state
  const [overrideStatus, setOverrideStatus] = useState<string>('');
  const [overrideReason, setOverrideReason] = useState<string>('');
  const [updating, setUpdating] = useState(false);
  const [updateMsg, setUpdateMsg] = useState<string | null>(null);

  useEffect(() => {
    if (!open || !defectId) return;

    let isMounted = true;
    const fetchDefect = async () => {
      try {
        setLoading(true);
        setError(null);
        setUpdateMsg(null);
        const data = await regressionService.getDefectDetail(defectId);
        if (isMounted) {
          setDefect(data);
          setOverrideStatus(data.status);
        }
      } catch (err: any) {
        if (isMounted) setError(err?.userMessage || 'Failed to fetch defect details.');
      } finally {
        if (isMounted) setLoading(false);
      }
    };
    fetchDefect();
    return () => {
      isMounted = false;
    };
  }, [open, defectId]);

  const handleStatusOverride = async () => {
    if (!defect || !overrideStatus || overrideStatus === defect.status) return;
    try {
      setUpdating(true);
      await regressionService.updateDefectStatus(
        defect.id,
        overrideStatus,
        overrideReason.trim() || undefined
      );
      setUpdateMsg(`Status updated to ${overrideStatus}.`);
      const updated = await regressionService.getDefectDetail(defect.id);
      setDefect(updated);
      if (onUpdated) onUpdated();
    } catch (err: any) {
      setError(err?.userMessage || 'Failed to update status.');
    } finally {
      setUpdating(false);
    }
  };

  const statusColor = (st: string) => {
    switch (st) {
      case 'New':
        return { bg: 'rgba(239, 68, 68, 0.2)', text: '#fca5a5' };
      case 'Open':
        return { bg: 'rgba(56, 189, 248, 0.2)', text: '#7dd3fc' };
      case 'Fixed':
        return { bg: 'rgba(34, 197, 94, 0.2)', text: '#86efac' };
      case 'Closed':
        return { bg: 'rgba(100, 116, 139, 0.2)', text: '#94a3b8' };
      case 'WontFix':
      case 'FalsePositive':
        return { bg: 'rgba(245, 158, 11, 0.2)', text: '#fcd34d' };
      default:
        return { bg: 'rgba(148, 163, 184, 0.2)', text: '#cbd5e1' };
    }
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle sx={{ m: 0, p: 2.5, bgcolor: '#0f172a', color: '#f8fafc', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Stack component="div" direction="row" spacing={1.5} sx={{ alignItems: 'center' }}>
          <BugReportIcon sx={{ color: '#38bdf8' }} />
          <Typography variant="h6" sx={{ fontWeight: 800 }}>
            {defect ? `${defect.defect_code} — Defect Lifecycle` : 'Defect Details'}
          </Typography>
        </Stack>
        <IconButton onClick={onClose} sx={{ color: '#94a3b8' }}>
          <CloseIcon />
        </IconButton>
      </DialogTitle>

      <DialogContent sx={{ p: 3, bgcolor: '#0b1120', minHeight: 450 }}>
        {loading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', py: 10 }}>
            <CircularProgress size={40} />
          </Box>
        ) : error || !defect ? (
          <Box sx={{ py: 6, textAlign: 'center' }}>
            <Typography color="error">{error || 'Defect not found.'}</Typography>
          </Box>
        ) : (
          <Stack component="div" spacing={3}>
            {updateMsg && (
              <Alert severity="success" sx={{ bgcolor: 'rgba(34, 197, 94, 0.1)', color: '#86efac' }}>
                {updateMsg}
              </Alert>
            )}

            {/* Overview Card */}
            <Paper sx={{ p: 2.5, bgcolor: '#1e293b', border: '1px solid #334155', borderRadius: 2 }}>
              <Stack
                component="div"
                direction={{ xs: 'column', sm: 'row' }}
                spacing={2}
                sx={{ justifyContent: 'space-between' }}
              >
                <Box>
                  <Typography variant="h6" sx={{ fontWeight: 700, color: '#f8fafc' }}>
                    {defect.title}
                  </Typography>
                  <Typography variant="caption" sx={{ color: '#94a3b8', display: 'block', mt: 0.5 }}>
                    WCAG: <strong>{defect.sc_code} {defect.sc_name}</strong> • Rule: {defect.rule_id}
                  </Typography>
                  <Typography variant="caption" sx={{ color: '#64748b', display: 'block', wordBreak: 'break-all' }}>
                    URL: {defect.page_url}
                  </Typography>
                </Box>

                <Stack component="div" direction="row" spacing={1} sx={{ alignItems: 'flex-start' }}>
                  <Chip
                    label={defect.severity}
                    size="small"
                    color={defect.severity === 'Critical' ? 'error' : defect.severity === 'Serious' ? 'warning' : 'primary'}
                    sx={{ fontWeight: 700 }}
                  />
                  <Chip
                    label={defect.status}
                    size="small"
                    sx={{
                      fontWeight: 800,
                      bgcolor: statusColor(defect.status).bg,
                      color: statusColor(defect.status).text
                    }}
                  />
                </Stack>
              </Stack>

              <Divider sx={{ my: 2, borderColor: '#334155' }} />

              {/* Lifecycle Metrics */}
              <Stack component="div" direction="row" spacing={3} sx={{ flexWrap: 'wrap' }}>
                <Box>
                  <Typography variant="caption" sx={{ color: '#94a3b8' }}>First Seen</Typography>
                  <Typography variant="body2" sx={{ fontWeight: 700, color: '#f8fafc' }}>
                    Run #{defect.first_seen_run_number}
                  </Typography>
                </Box>
                <Box>
                  <Typography variant="caption" sx={{ color: '#94a3b8' }}>Last Seen</Typography>
                  <Typography variant="body2" sx={{ fontWeight: 700, color: '#f8fafc' }}>
                    Run #{defect.last_seen_run_number}
                  </Typography>
                </Box>
                <Box>
                  <Typography variant="caption" sx={{ color: '#94a3b8' }}>Times Seen</Typography>
                  <Typography variant="body2" sx={{ fontWeight: 700, color: '#f8fafc' }}>
                    {defect.times_seen} run(s)
                  </Typography>
                </Box>
                <Box>
                  <Typography variant="caption" sx={{ color: '#94a3b8' }}>Reopen Count</Typography>
                  <Typography variant="body2" sx={{ fontWeight: 700, color: defect.reopen_count > 0 ? '#f59e0b' : '#f8fafc' }}>
                    {defect.reopen_count}
                  </Typography>
                </Box>
                <Box>
                  <Typography variant="caption" sx={{ color: '#94a3b8' }}>Defect Age</Typography>
                  <Typography variant="body2" sx={{ fontWeight: 700, color: '#f8fafc' }}>
                    {defect.age_days} day(s)
                  </Typography>
                </Box>
              </Stack>
            </Paper>

            {/* Status Override Control */}
            <Paper sx={{ p: 2.5, bgcolor: '#1e293b', border: '1px solid #334155', borderRadius: 2 }}>
              <Typography variant="subtitle2" sx={{ fontWeight: 700, color: '#f8fafc', mb: 1.5 }}>
                Auditor Status Override
              </Typography>
              <Stack
                component="div"
                direction={{ xs: 'column', sm: 'row' }}
                spacing={2}
                sx={{ alignItems: 'center' }}
              >
                <FormControl size="small" sx={{ minWidth: 160 }}>
                  <InputLabel sx={{ color: '#94a3b8' }}>Override Status</InputLabel>
                  <Select
                    value={overrideStatus}
                    label="Override Status"
                    onChange={(e) => setOverrideStatus(e.target.value)}
                    sx={{ color: '#f8fafc', '& .MuiOutlinedInput-notchedOutline': { borderColor: '#475569' } }}
                  >
                    <MenuItem value="Open">Open</MenuItem>
                    <MenuItem value="WontFix">Won't Fix</MenuItem>
                    <MenuItem value="FalsePositive">False Positive</MenuItem>
                  </Select>
                </FormControl>
                <TextField
                  size="small"
                  fullWidth
                  placeholder="Reason for status override (e.g. Design exception, third-party widget)"
                  value={overrideReason}
                  onChange={(e) => setOverrideReason(e.target.value)}
                  sx={{
                    '& .MuiOutlinedInput-root': {
                      color: '#f8fafc',
                      '& fieldset': { borderColor: '#475569' }
                    }
                  }}
                />
                <Button
                  variant="contained"
                  onClick={handleStatusOverride}
                  disabled={updating || overrideStatus === defect.status}
                  sx={{ minWidth: 100, textTransform: 'none', fontWeight: 700 }}
                >
                  {updating ? <CircularProgress size={20} /> : 'Apply'}
                </Button>
              </Stack>
            </Paper>

            {/* Event Timeline */}
            <Paper sx={{ p: 2.5, bgcolor: '#1e293b', border: '1px solid #334155', borderRadius: 2 }}>
              <Stack component="div" direction="row" spacing={1} sx={{ alignItems: 'center', mb: 2 }}>
                <HistoryIcon sx={{ color: '#94a3b8' }} />
                <Typography variant="subtitle2" sx={{ fontWeight: 700, color: '#f8fafc' }}>
                  Audit History & Regression Timeline
                </Typography>
              </Stack>

              <Stack component="div" spacing={1.5}>
                {defect.timeline && defect.timeline.length > 0 ? (
                  defect.timeline.map((evt, idx) => (
                    <Box
                      key={idx}
                      sx={{
                        p: 1.5,
                        bgcolor: '#0f172a',
                        borderLeft: '3px solid',
                        borderColor:
                          evt.event === 'auto_fixed'
                            ? '#22c55e'
                            : evt.event === 'reopened'
                            ? '#f59e0b'
                            : evt.event === 'detected'
                            ? '#ef4444'
                            : '#38bdf8',
                        borderRadius: '0 6px 6px 0'
                      }}
                    >
                      <Stack
                        component="div"
                        direction="row"
                        sx={{ justifyContent: 'space-between', alignItems: 'center' }}
                      >
                        <Stack component="div" direction="row" spacing={1} sx={{ alignItems: 'center' }}>
                          <Chip
                            label={evt.event.toUpperCase()}
                            size="small"
                            sx={{ fontWeight: 800, fontSize: '0.65rem' }}
                          />
                          <Typography variant="body2" sx={{ fontWeight: 600, color: '#f8fafc' }}>
                            {evt.from_status ? `${evt.from_status} → ${evt.to_status}` : evt.to_status}
                          </Typography>
                        </Stack>
                        <Typography variant="caption" sx={{ color: '#64748b' }}>
                          {new Date(evt.created_at).toLocaleString()}
                        </Typography>
                      </Stack>
                      {evt.note && (
                        <Typography variant="caption" sx={{ color: '#94a3b8', mt: 0.5, display: 'block' }}>
                          {evt.note}
                        </Typography>
                      )}
                    </Box>
                  ))
                ) : (
                  <Typography variant="body2" sx={{ color: '#64748b' }}>No timeline events recorded.</Typography>
                )}
              </Stack>
            </Paper>

            {/* Code Evidence */}
            {defect.code_before && (
              <Paper sx={{ p: 2.5, bgcolor: '#1e293b', border: '1px solid #334155', borderRadius: 2 }}>
                <Typography variant="subtitle2" sx={{ fontWeight: 700, color: '#f8fafc', mb: 1 }}>
                  HTML Snippet
                </Typography>
                <Box
                  sx={{
                    p: 1.5,
                    bgcolor: '#0f172a',
                    borderRadius: 1,
                    fontFamily: 'monospace',
                    fontSize: '0.8rem',
                    color: '#fca5a5',
                    overflowX: 'auto'
                  }}
                >
                  {defect.code_before}
                </Box>
              </Paper>
            )}
          </Stack>
        )}
      </DialogContent>

      <DialogActions sx={{ p: 2, bgcolor: '#0f172a', borderTop: '1px solid #1e293b' }}>
        <Button onClick={onClose} variant="contained">
          Close
        </Button>
      </DialogActions>
    </Dialog>
  );
};
