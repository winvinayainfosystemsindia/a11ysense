import React, { useState, useEffect } from 'react';
import {
  Drawer,
  Box,
  Typography,
  Stack,
  IconButton,
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
  Button,
  CircularProgress,
  Tooltip,
  TextField,
  MenuItem,
  Select,
  FormControl,
  InputLabel
} from '@mui/material';
import CloseIcon from '@mui/icons-material/Close';
import CompareArrowsIcon from '@mui/icons-material/CompareArrows';
import LaunchIcon from '@mui/icons-material/Launch';
import BugReportIcon from '@mui/icons-material/BugReport';
import TimelineIcon from '@mui/icons-material/Timeline';

import type { ProjectResponse } from '../../model/project.model';
import type { ProjectRun, ProjectTrendItem } from '../../model/regression.model';
import { regressionService } from '../../service/regressionService';
import { RunComparisonModal } from '../audits/details/RunComparisonModal';
import { DefectDetailModal } from '../audits/details/DefectDetailModal';

interface Props {
  open: boolean;
  onClose: () => void;
  project: ProjectResponse | null;
}

export const ProjectRunsDrawer: React.FC<Props> = ({ open, onClose, project }) => {
  const [tabIndex, setTabIndex] = useState(0);
  const [runs, setRuns] = useState<ProjectRun[]>([]);
  const [trend, setTrend] = useState<ProjectTrendItem[]>([]);
  const [defects, setDefects] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  // Filters for defects
  const [defectStatusFilter, setDefectStatusFilter] = useState('ALL');
  const [defectSearch, setDefectSearch] = useState('');

  // Modals
  const [compareModal, setCompareModal] = useState<{ open: boolean; taskA: string; taskB: string }>({
    open: false,
    taskA: '',
    taskB: ''
  });
  const [defectModalId, setDefectModalId] = useState<string | null>(null);

  useEffect(() => {
    if (!open || !project) return;
    let isMounted = true;

    const loadData = async () => {
      try {
        setLoading(true);
        const [runsData, trendData, defectsData] = await Promise.all([
          regressionService.getProjectRuns(project.id),
          regressionService.getProjectTrend(project.id),
          regressionService.getProjectDefects(project.id)
        ]);
        if (isMounted) {
          setRuns(runsData);
          setTrend(trendData.runs || []);
          setDefects(defectsData);
        }
      } catch (err) {
        console.error('Failed to load project regression data:', err);
      } finally {
        if (isMounted) setLoading(false);
      }
    };

    loadData();
    return () => {
      isMounted = false;
    };
  }, [open, project]);

  if (!project) return null;

  const filteredDefects = defects.filter((d) => {
    if (defectStatusFilter !== 'ALL' && d.status !== defectStatusFilter) return false;
    if (defectSearch) {
      const q = defectSearch.toLowerCase();
      return (
        d.defect_code?.toLowerCase().includes(q) ||
        d.rule_id?.toLowerCase().includes(q) ||
        d.title?.toLowerCase().includes(q) ||
        d.page_url?.toLowerCase().includes(q)
      );
    }
    return true;
  });

  return (
    <>
      <Drawer
        anchor="right"
        open={open}
        onClose={onClose}
        sx={{
          '& .MuiDrawer-paper': {
            width: { xs: '100%', md: 850 },
            bgcolor: '#0b1120',
            color: '#f8fafc',
            p: 3
          }
        }}
      >
        {/* Drawer Header */}
        <Stack
          component="div"
          direction="row"
          sx={{ justifyContent: 'space-between', alignItems: 'center', mb: 2 }}
        >
          <Box>
            <Typography variant="h5" sx={{ fontWeight: 800, color: '#f8fafc' }}>
              {project.name}
            </Typography>
            <Typography variant="caption" sx={{ color: '#94a3b8' }}>
              Target: {project.base_url || 'N/A'} • Type: {project.project_type}
            </Typography>
          </Box>
          <IconButton onClick={onClose} sx={{ color: '#94a3b8' }}>
            <CloseIcon />
          </IconButton>
        </Stack>

        {/* Tabs */}
        <Box sx={{ borderBottom: 1, borderColor: '#334155', mb: 3 }}>
          <Tabs value={tabIndex} onChange={(_, val) => setTabIndex(val)} textColor="primary" indicatorColor="primary">
            <Tab
              icon={<TimelineIcon sx={{ fontSize: 18 }} />}
              iconPosition="start"
              label={`Audit Runs & Trend (${runs.length})`}
              sx={{ fontWeight: 700, textTransform: 'none', color: '#94a3b8' }}
            />
            <Tab
              icon={<BugReportIcon sx={{ fontSize: 18 }} />}
              iconPosition="start"
              label={`Project Defects (${defects.length})`}
              sx={{ fontWeight: 700, textTransform: 'none', color: '#94a3b8' }}
            />
          </Tabs>
        </Box>

        {loading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', py: 10 }}>
            <CircularProgress size={40} />
          </Box>
        ) : (
          <>
            {/* TAB 0: Runs & Trend */}
            {tabIndex === 0 && (
              <Stack component="div" spacing={3}>
                {/* Visual Trend Chart */}
                {trend.length > 1 && (
                  <Paper
                    sx={{
                      p: 2.5,
                      bgcolor: '#1e293b',
                      border: '1px solid #334155',
                      borderRadius: 2
                    }}
                  >
                    <Typography variant="subtitle2" sx={{ fontWeight: 700, color: '#f8fafc', mb: 2 }}>
                      Accessibility Score Trajectory Over Runs
                    </Typography>
                    <TrendChart runs={trend} />
                  </Paper>
                )}

                {/* Runs Table */}
                <Typography variant="subtitle2" sx={{ fontWeight: 700, color: '#f8fafc' }}>
                  Execution History
                </Typography>
                {runs.length === 0 ? (
                  <Box sx={{ py: 6, textAlign: 'center' }}>
                    <Typography variant="body2" sx={{ color: '#64748b' }}>
                      No audit runs executed yet for this project.
                    </Typography>
                  </Box>
                ) : (
                  <TableContainer component={Paper} sx={{ bgcolor: '#0f172a', border: '1px solid #1e293b' }}>
                    <Table size="small">
                      <TableHead>
                        <TableRow sx={{ bgcolor: '#1e293b' }}>
                          <TableCell sx={{ color: '#94a3b8', fontWeight: 700 }}>Run #</TableCell>
                          <TableCell sx={{ color: '#94a3b8', fontWeight: 700 }}>Type</TableCell>
                          <TableCell sx={{ color: '#94a3b8', fontWeight: 700 }}>Score</TableCell>
                          <TableCell sx={{ color: '#94a3b8', fontWeight: 700 }}>Defects Reconciliation</TableCell>
                          <TableCell sx={{ color: '#94a3b8', fontWeight: 700 }}>Date</TableCell>
                          <TableCell sx={{ color: '#94a3b8', fontWeight: 700 }} align="right">Actions</TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {runs.map((r, idx) => {
                          const prevRun = idx < runs.length - 1 ? runs[idx + 1] : null;
                          return (
                            <TableRow key={r.id} hover>
                              <TableCell sx={{ color: '#f8fafc', fontWeight: 800 }}>
                                #{r.run_number}
                              </TableCell>
                              <TableCell>
                                <Chip
                                  label={r.run_type === 'baseline' ? 'Baseline' : 'Regression'}
                                  size="small"
                                  color={r.run_type === 'baseline' ? 'primary' : 'secondary'}
                                  variant="outlined"
                                  sx={{ fontWeight: 700, fontSize: '0.65rem' }}
                                />
                              </TableCell>
                              <TableCell>
                                <Stack component="div" direction="row" spacing={0.5} sx={{ alignItems: 'center' }}>
                                  <Typography variant="body2" sx={{ fontWeight: 800, color: '#f8fafc' }}>
                                    {r.score}%
                                  </Typography>
                                  {r.run_type !== 'baseline' && r.score_delta !== 0 && (
                                    <Chip
                                      label={`${r.score_delta > 0 ? '+' : ''}${r.score_delta}%`}
                                      size="small"
                                      sx={{
                                        fontSize: '0.65rem',
                                        fontWeight: 800,
                                        bgcolor: r.score_delta > 0 ? 'rgba(34, 197, 94, 0.15)' : 'rgba(239, 68, 68, 0.15)',
                                        color: r.score_delta > 0 ? '#4ade80' : '#f87171'
                                      }}
                                    />
                                  )}
                                </Stack>
                              </TableCell>
                              <TableCell>
                                <Stack component="div" direction="row" spacing={1} sx={{ alignItems: 'center' }}>
                                  {r.defects_fixed > 0 && (
                                    <Tooltip title={`${r.defects_fixed} defects fixed`}>
                                      <Chip label={`✓ ${r.defects_fixed}`} size="small" color="success" sx={{ fontSize: '0.65rem', height: 20 }} />
                                    </Tooltip>
                                  )}
                                  {r.defects_new > 0 && (
                                    <Tooltip title={`${r.defects_new} new defects`}>
                                      <Chip label={`+ ${r.defects_new}`} size="small" color="error" sx={{ fontSize: '0.65rem', height: 20 }} />
                                    </Tooltip>
                                  )}
                                  {r.defects_reopened > 0 && (
                                    <Tooltip title={`${r.defects_reopened} reopened defects`}>
                                      <Chip label={`↺ ${r.defects_reopened}`} size="small" color="warning" sx={{ fontSize: '0.65rem', height: 20 }} />
                                    </Tooltip>
                                  )}
                                  <Tooltip title={`${r.defects_open} still open`}>
                                    <Chip label={`● ${r.defects_open}`} size="small" color="info" sx={{ fontSize: '0.65rem', height: 20 }} />
                                  </Tooltip>
                                </Stack>
                              </TableCell>
                              <TableCell sx={{ color: '#94a3b8', fontSize: '0.75rem' }}>
                                {r.completed_at ? new Date(r.completed_at).toLocaleDateString() : '-'}
                              </TableCell>
                              <TableCell align="right">
                                <Stack component="div" direction="row" spacing={0.5} sx={{ justifyContent: 'flex-end' }}>
                                  {prevRun && (
                                    <Tooltip title={`Compare Run #${r.run_number} vs Run #${prevRun.run_number}`}>
                                      <IconButton
                                        size="small"
                                        onClick={() =>
                                          setCompareModal({
                                            open: true,
                                            taskA: prevRun.task_id,
                                            taskB: r.task_id
                                          })
                                        }
                                        sx={{ color: '#94a3b8' }}
                                      >
                                        <CompareArrowsIcon fontSize="small" />
                                      </IconButton>
                                    </Tooltip>
                                  )}
                                  <Button
                                    size="small"
                                    component="a"
                                    href={`/audits/${r.task_id}`}
                                    startIcon={<LaunchIcon sx={{ fontSize: 14 }} />}
                                    sx={{ textTransform: 'none', fontWeight: 700, fontSize: '0.75rem' }}
                                  >
                                    View
                                  </Button>
                                </Stack>
                              </TableCell>
                            </TableRow>
                          );
                        })}
                      </TableBody>
                    </Table>
                  </TableContainer>
                )}
              </Stack>
            )}

            {/* TAB 1: Project Defects */}
            {tabIndex === 1 && (
              <Stack component="div" spacing={2}>
                {/* Search & Status Filter */}
                <Stack component="div" direction="row" spacing={2} sx={{ alignItems: 'center' }}>
                  <TextField
                    size="small"
                    placeholder="Search by defect code, rule, or URL..."
                    value={defectSearch}
                    onChange={(e) => setDefectSearch(e.target.value)}
                    sx={{
                      flex: 1,
                      '& .MuiOutlinedInput-root': {
                        color: '#f8fafc',
                        '& fieldset': { borderColor: '#475569' }
                      }
                    }}
                  />
                  <FormControl size="small" sx={{ minWidth: 150 }}>
                    <InputLabel sx={{ color: '#94a3b8' }}>Status</InputLabel>
                    <Select
                      value={defectStatusFilter}
                      label="Status"
                      onChange={(e) => setDefectStatusFilter(e.target.value)}
                      sx={{ color: '#f8fafc', '& .MuiOutlinedInput-notchedOutline': { borderColor: '#475569' } }}
                    >
                      <MenuItem value="ALL">All Statuses</MenuItem>
                      <MenuItem value="New">New</MenuItem>
                      <MenuItem value="Open">Open</MenuItem>
                      <MenuItem value="Fixed">Fixed</MenuItem>
                      <MenuItem value="Closed">Closed</MenuItem>
                      <MenuItem value="WontFix">Won't Fix</MenuItem>
                      <MenuItem value="FalsePositive">False Positive</MenuItem>
                    </Select>
                  </FormControl>
                </Stack>

                {/* Defects Table */}
                <TableContainer component={Paper} sx={{ bgcolor: '#0f172a', border: '1px solid #1e293b' }}>
                  <Table size="small">
                    <TableHead>
                      <TableRow sx={{ bgcolor: '#1e293b' }}>
                        <TableCell sx={{ color: '#94a3b8', fontWeight: 700 }}>Defect Code</TableCell>
                        <TableCell sx={{ color: '#94a3b8', fontWeight: 700 }}>Rule / Title</TableCell>
                        <TableCell sx={{ color: '#94a3b8', fontWeight: 700 }}>Severity</TableCell>
                        <TableCell sx={{ color: '#94a3b8', fontWeight: 700 }}>Status</TableCell>
                        <TableCell sx={{ color: '#94a3b8', fontWeight: 700 }}>Runs</TableCell>
                        <TableCell sx={{ color: '#94a3b8', fontWeight: 700 }} align="right">Timeline</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {filteredDefects.map((d) => (
                        <TableRow key={d.id} hover>
                          <TableCell sx={{ color: '#f8fafc', fontWeight: 800, fontFamily: 'monospace' }}>
                            {d.defect_code}
                          </TableCell>
                          <TableCell sx={{ color: '#cbd5e1', maxWidth: 220 }}>
                            <Typography variant="body2" sx={{ fontWeight: 600 }}>{d.title || d.rule_id}</Typography>
                            <Typography variant="caption" sx={{ color: '#64748b' }}>{d.sc_code}</Typography>
                          </TableCell>
                          <TableCell>
                            <Chip
                              label={d.severity}
                              size="small"
                              color={d.severity === 'Critical' ? 'error' : d.severity === 'Serious' ? 'warning' : 'primary'}
                              sx={{ fontWeight: 700, fontSize: '0.65rem' }}
                            />
                          </TableCell>
                          <TableCell>
                            <Chip
                              label={d.status}
                              size="small"
                              sx={{
                                fontWeight: 800,
                                fontSize: '0.65rem',
                                bgcolor:
                                  d.status === 'Fixed'
                                    ? 'rgba(34, 197, 94, 0.15)'
                                    : d.status === 'New'
                                    ? 'rgba(239, 68, 68, 0.15)'
                                    : d.status === 'Reopened'
                                    ? 'rgba(245, 158, 11, 0.15)'
                                    : 'rgba(56, 189, 248, 0.15)',
                                color:
                                  d.status === 'Fixed'
                                    ? '#4ade80'
                                    : d.status === 'New'
                                    ? '#f87171'
                                    : d.status === 'Reopened'
                                    ? '#fbbf24'
                                    : '#38bdf8'
                              }}
                            />
                          </TableCell>
                          <TableCell sx={{ color: '#94a3b8', fontSize: '0.75rem' }}>
                            {d.times_seen} run(s)
                            {d.reopen_count > 0 && ` • ↺ ${d.reopen_count}`}
                          </TableCell>
                          <TableCell align="right">
                            <Button
                              size="small"
                              variant="outlined"
                              onClick={() => setDefectModalId(d.id)}
                              sx={{ textTransform: 'none', fontWeight: 700, fontSize: '0.75rem' }}
                            >
                              Timeline
                            </Button>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              </Stack>
            )}
          </>
        )}
      </Drawer>

      {/* Comparison Modal */}
      {compareModal.open && (
        <RunComparisonModal
          open={compareModal.open}
          onClose={() => setCompareModal({ open: false, taskA: '', taskB: '' })}
          currentTaskId={compareModal.taskB}
          previousTaskId={compareModal.taskA}
        />
      )}

      {/* Defect Modal */}
      {defectModalId && (
        <DefectDetailModal
          open={Boolean(defectModalId)}
          onClose={() => setDefectModalId(null)}
          defectId={defectModalId}
          onUpdated={async () => {
            const defs = await regressionService.getProjectDefects(project.id);
            setDefects(defs);
          }}
        />
      )}
    </>
  );
};

// ── SVG Trend Visualizer Component ──────────────────────────────────────────

const TrendChart: React.FC<{ runs: ProjectTrendItem[] }> = ({ runs }) => {
  const sorted = [...runs].sort((a, b) => a.run_number - b.run_number);
  const width = 760;
  const height = 140;
  const padding = 35;

  if (sorted.length < 2) return null;

  const minScore = 0;
  const maxScore = 100;
  const xStep = (width - padding * 2) / (sorted.length - 1);

  const points = sorted.map((r, i) => {
    const x = padding + i * xStep;
    const y = height - padding - ((r.score - minScore) / (maxScore - minScore)) * (height - padding * 2);
    return { x, y, run: r };
  });

  const pathD = points.reduce((acc, p, i) => `${acc} ${i === 0 ? 'M' : 'L'} ${p.x} ${p.y}`, '');

  return (
    <Box sx={{ width: '100%', overflowX: 'auto' }}>
      <svg width={width} height={height} style={{ display: 'block', margin: '0 auto' }}>
        <line x1={padding} y1={height - padding} x2={width - padding} y2={height - padding} stroke="#334155" strokeDasharray="3 3" />
        <line x1={padding} y1={padding} x2={width - padding} y2={padding} stroke="#334155" strokeDasharray="3 3" />

        <text x={padding - 8} y={height - padding + 4} fill="#64748b" fontSize="10" textAnchor="end">0%</text>
        <text x={padding - 8} y={padding + 4} fill="#64748b" fontSize="10" textAnchor="end">100%</text>

        <path d={pathD} fill="none" stroke="#38bdf8" strokeWidth="2.5" />

        {points.map((p, i) => (
          <g key={i}>
            <circle cx={p.x} cy={p.y} r="4.5" fill="#0284c7" stroke="#f8fafc" strokeWidth="2" />
            <text x={p.x} y={p.y - 10} fill="#f8fafc" fontSize="11" fontWeight="bold" textAnchor="middle">
              {p.run.score}%
            </text>
            <text x={p.x} y={height - 10} fill="#94a3b8" fontSize="10" textAnchor="middle">
              Run #{p.run.run_number}
            </text>
          </g>
        ))}
      </svg>
    </Box>
  );
};
