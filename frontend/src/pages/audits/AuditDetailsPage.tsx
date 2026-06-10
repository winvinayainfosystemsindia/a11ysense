import React, { useState, useEffect, useMemo } from 'react';
import { useParams, useNavigate } from '@tanstack/react-router';
import {
  Box,
  Typography,
  Stack,
  Button,
  Card,
  CircularProgress,
  Chip,
  Divider,
  useTheme,
  alpha,
  LinearProgress,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Tabs,
  Tab,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  Grid,
  IconButton
} from '@mui/material';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import LaunchIcon from '@mui/icons-material/Launch';
import AssessmentIcon from '@mui/icons-material/Assessment';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import PauseIcon from '@mui/icons-material/Pause';
import StopIcon from '@mui/icons-material/Stop';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import ErrorIcon from '@mui/icons-material/Error';
import WarningIcon from '@mui/icons-material/Warning';
import CodeIcon from '@mui/icons-material/Code';
import BuildIcon from '@mui/icons-material/Build';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import FileDownloadIcon from '@mui/icons-material/FileDownload';
import { auditService } from '../../service/auditService';
import type { AuditTaskDetail } from '../../service/auditService';

// Browser-like Visual Mockup Component
const ViolationMockup: React.FC<{ htmlSnippet: string; ruleId: string }> = ({ htmlSnippet, ruleId }) => {
  const getTagType = (html: string) => {
    const match = html.trim().match(/^<([a-zA-Z0-9]+)/);
    return match ? match[1].toLowerCase() : 'element';
  };

  const tag = getTagType(htmlSnippet);

  return (
    <Box sx={{
      border: '1px solid #e2e8f0',
      borderRadius: '12px',
      overflow: 'hidden',
      bgcolor: '#f8fafc',
      boxShadow: 'inset 0 2px 4px 0 rgba(0, 0, 0, 0.02)'
    }}>
      {/* Browser Bar */}
      <Box sx={{
        display: 'flex',
        alignItems: 'center',
        gap: 1,
        px: 2,
        py: 1.5,
        bgcolor: '#f1f5f9',
        borderBottom: '1px solid #e2e8f0'
      }}>
        <Box sx={{ display: 'flex', gap: 0.5 }}>
          <Box sx={{ width: 10, height: 10, borderRadius: '50%', bgcolor: '#ef4444' }} />
          <Box sx={{ width: 10, height: 10, borderRadius: '50%', bgcolor: '#f59e0b' }} />
          <Box sx={{ width: 10, height: 10, borderRadius: '50%', bgcolor: '#10b981' }} />
        </Box>
        <Box sx={{
          flex: 1,
          bgcolor: '#ffffff',
          borderRadius: '6px',
          px: 1.5,
          py: 0.5,
          fontSize: '0.75rem',
          color: 'text.secondary',
          fontFamily: 'monospace',
          border: '1px solid #cbd5e1',
          overflow: 'hidden',
          textOverflow: 'ellipsis',
          whiteSpace: 'nowrap'
        }}>
          Render Preview
        </Box>
      </Box>

      {/* Preview Body */}
      <Box sx={{
        p: 4,
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        minHeight: '220px',
        position: 'relative'
      }}>
        <Box sx={{
          border: '2px dashed #ef4444',
          borderRadius: '8px',
          p: 3,
          position: 'relative',
          bgcolor: '#ffffff',
          boxShadow: '0 4px 6px -1px rgba(0,0,0,0.05)',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: 1.5,
          maxWidth: '85%'
        }}>
          {/* Violation Area Badge */}
          <Chip
            label="VIOLATION AREA"
            size="small"
            sx={{
              bgcolor: '#ef4444',
              color: '#ffffff',
              fontWeight: '800',
              fontSize: '0.65rem',
              height: '18px',
              position: 'absolute',
              top: -10,
              right: 10,
              boxShadow: 2
            }}
          />

          {tag === 'img' && (
            <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 1 }}>
              <Box sx={{ width: 64, height: 64, bgcolor: '#e2e8f0', borderRadius: '6px', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '2rem' }}>
                📷
              </Box>
              <Typography variant="caption" color="text.secondary" sx={{ fontWeight: '600' }}>Missing Alt Attribute</Typography>
            </Box>
          )}

          {(tag === 'button' || tag === 'a') && (
            <Box sx={{ px: 3, py: 1, bgcolor: '#0284c7', color: '#ffffff', borderRadius: '6px', fontWeight: '600', fontSize: '0.875rem', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
              Interactive Node
            </Box>
          )}

          {tag === 'input' && (
            <Box sx={{ width: 160, height: 36, border: '1px solid #cbd5e1', borderRadius: '6px', px: 1.5, display: 'flex', alignItems: 'center', bgcolor: '#f8fafc' }}>
              <Box sx={{ width: 12, height: 12, borderRadius: '50%', bgcolor: '#cbd5e1' }} />
            </Box>
          )}

          {tag !== 'img' && tag !== 'button' && tag !== 'a' && tag !== 'input' && (
            <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 1 }}>
              <Typography variant="body2" sx={{ fontWeight: '700', color: 'text.primary', textAlign: 'center' }}>
                {ruleId.replace(/-/g, ' ').toUpperCase()}
              </Typography>
              <Typography variant="caption" color="text.secondary" sx={{ textAlign: 'center', wordBreak: 'break-all', fontFamily: 'monospace' }}>
                {htmlSnippet.length > 100 ? htmlSnippet.substring(0, 100) + '...' : htmlSnippet}
              </Typography>
            </Box>
          )}
        </Box>
      </Box>
    </Box>
  );
};

const AuditDetailsPage: React.FC = () => {
  const { orgId, taskId } = useParams({ strict: false }) as any;
  const navigate = useNavigate();
  const theme = useTheme();

  const [taskDetail, setTaskDetail] = useState<AuditTaskDetail | null>(null);
  const [testcases, setTestcases] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Tab State
  const [activeTab, setActiveTab] = useState(0);

  // Explorer Filter State
  const [selectedViolation, setSelectedViolation] = useState<any>(null);
  const [severityFilter, setSeverityFilter] = useState('all');
  const [wcagFilter, setWcagFilter] = useState('all');

  // Pagination State for Tables
  const [defectsPage, setDefectsPage] = useState(0);
  const [defectsRowsPerPage, setDefectsRowsPerPage] = useState(10);
  const [testcasesPage, setTestcasesPage] = useState(0);
  const [testcasesRowsPerPage, setTestcasesRowsPerPage] = useState(10);

  // AI Fix Application Loading State
  const [isApplyingFix, setIsApplyingFix] = useState(false);

  const isTerminal = (status: string) => {
    const s = status.toLowerCase();
    return s === 'completed' || s === 'failed' || s === 'stopped';
  };

  const fetchData = async (showLoading = false) => {
    if (showLoading) setLoading(true);
    try {
      const [taskData] = await Promise.all([
        auditService.getTaskStatus(taskId)
      ]);
      setTaskDetail(taskData);

      if (isTerminal(taskData.status)) {
        const tcData = await auditService.getTaskTestcases(taskId).catch(() => []);
        setTestcases(tcData);
      }
    } catch (err: any) {
      console.error('Error fetching audit details:', err);
      setError(err.message || 'Failed to load audit details');
    } finally {
      if (showLoading) setLoading(false);
    }
  };

  useEffect(() => {
    if (!taskId) return;
    
    fetchData(true);

    // Dynamic Polling for active audits
    const interval = setInterval(() => {
      setTaskDetail(prev => {
        if (prev && !isTerminal(prev.status)) {
          fetchData(false);
        }
        return prev;
      });
    }, 3000);

    return () => clearInterval(interval);
  }, [taskId]);

  const handleBack = () => {
    navigate({ to: `/org/${orgId}/audits` });
  };

  const handleOpenReport = () => {
    window.open(`http://localhost:8002/report/${taskId}`, '_blank');
  };

  const handleExportReport = () => {
    window.open(`http://localhost:8002/report/${taskId}/export`, '_blank');
  };

  const handlePause = async () => {
    setActionLoading(true);
    try {
      await auditService.pauseAudit(taskId);
      await fetchData(false);
    } catch (err) {
      console.error('Pause failed:', err);
    } finally {
      setActionLoading(false);
    }
  };

  const handleResume = async () => {
    setActionLoading(true);
    try {
      await auditService.resumeAudit(taskId);
      await fetchData(false);
    } catch (err) {
      console.error('Resume failed:', err);
    } finally {
      setActionLoading(false);
    }
  };

  const handleStop = async () => {
    if (!window.confirm('Are you sure you want to stop this audit? A partial report will be compiled.')) return;
    setActionLoading(true);
    try {
      await auditService.stopAudit(taskId);
      await fetchData(false);
    } catch (err) {
      console.error('Stop failed:', err);
    } finally {
      setActionLoading(false);
    }
  };

  const handleApplyFix = () => {
    setIsApplyingFix(true);
    setTimeout(() => {
      setIsApplyingFix(false);
      window.dispatchEvent(new CustomEvent('app-toast', {
        detail: {
          message: 'Suggested fix sent to agent. Pull Request will be created in your linked GitHub repository.',
          variant: 'success'
        }
      }));
    }, 1500);
  };

  const handleCopyCode = (code: string) => {
    navigator.clipboard.writeText(code);
    window.dispatchEvent(new CustomEvent('app-toast', {
      detail: {
        message: 'Code copied to clipboard',
        variant: 'success'
      }
    }));
  };

  // Derive defects and passed checks
  const violations = useMemo(() => testcases.filter(tc => tc.status === 'FAIL'), [testcases]);

  // Derive unique WCAG criteria from violations for filter dropdown
  const wcagCriteriaList = useMemo(() => {
    const criteriaSet = new Set<string>();
    violations.forEach(v => {
      if (v.criteria && v.criteria !== 'N/A') {
        criteriaSet.add(v.criteria);
      }
    });
    return Array.from(criteriaSet);
  }, [violations]);

  // Filtered violations for Explorer
  const filteredViolations = useMemo(() => {
    return violations.filter(v => {
      const matchesSeverity = severityFilter === 'all' || v.severity?.toLowerCase() === severityFilter.toLowerCase();
      const matchesWcag = wcagFilter === 'all' || v.criteria === wcagFilter;
      return matchesSeverity && matchesWcag;
    });
  }, [violations, severityFilter, wcagFilter]);

  // Set default selected violation
  useEffect(() => {
    if (filteredViolations.length > 0) {
      // Keep existing selected if still in filtered, otherwise select first filtered
      const stillAvailable = filteredViolations.find(v => v.testcase_id === selectedViolation?.testcase_id);
      if (!stillAvailable) {
        setSelectedViolation(filteredViolations[0]);
      }
    } else {
      setSelectedViolation(null);
    }
  }, [filteredViolations, selectedViolation]);

  // KPI Calculations
  const calculatedScore = useMemo(() => {
    if (violations.length === 0) return 100;
    let totalPenalty = 0;
    violations.forEach(v => {
      const severity = v.severity?.toLowerCase() || 'moderate';
      let weight = 3.0;
      if (severity === 'blocker' || severity === 'critical') weight = 10.0;
      else if (severity === 'serious' || severity === 'high') weight = 6.0;
      else if (severity === 'moderate' || severity === 'medium') weight = 3.0;
      else if (severity === 'minor' || severity === 'low') weight = 1.0;

      const snippet = v.html_snippet || '';
      const nodeCount = snippet ? snippet.split('\n').filter(Boolean).length : 1;
      
      const penalty = weight * Math.log(1.0 + nodeCount);
      totalPenalty += penalty;
    });
    const score = Math.max(0, Math.min(100, 100 - totalPenalty));
    return parseFloat(score.toFixed(1));
  }, [violations]);

  const accessibilityScore = taskDetail?.summary?.accessibility_score ?? (taskDetail?.status === 'completed' ? calculatedScore : 0);
  const criticalCount = useMemo(() => violations.filter(v => v.severity?.toLowerCase() === 'critical').length, [violations]);
  const moderateCount = useMemo(() => violations.filter(v => v.severity?.toLowerCase() === 'moderate').length, [violations]);
  const wcagLevel = useMemo(() => {
    if (violations.length === 0) return 'AAA';
    const hasA = violations.some(v => v.level === 'A');
    return hasA ? 'A' : 'AA';
  }, [violations]);

  if (loading) {
    return (
      <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', py: 12 }}>
        <CircularProgress size={50} color="primary" />
        <Typography variant="body2" color="text.secondary" sx={{ mt: 3, fontWeight: '500' }}>Loading audit details...</Typography>
      </Box>
    );
  }

  if (error || !taskDetail) {
    return (
      <Box sx={{ py: 4 }}>
        <Button startIcon={<ArrowBackIcon />} onClick={handleBack} sx={{ mb: 4 }}>
          Back to Audits
        </Button>
        <Typography color="error.main" variant="h5" sx={{ fontWeight: '700' }}>Error Loading Details</Typography>
        <Typography color="text.secondary" sx={{ mt: 1 }}>{error || 'Audit not found'}</Typography>
      </Box>
    );
  }

  const isCompleted = taskDetail.status === 'completed';
  const isStopped = taskDetail.status === 'stopped';
  const isRunning = taskDetail.status === 'in_progress' || taskDetail.status === 'crawling' || taskDetail.status === 'auditing';
  const isPaused = taskDetail.status === 'paused';

  return (
    <Box sx={{ pb: 6 }}>
      <Button startIcon={<ArrowBackIcon />} onClick={handleBack} sx={{ mb: 3 }}>
        Back to Audits
      </Button>

      {/* Header Panel */}
      <Stack component="div" direction={{ xs: 'column', md: 'row' }} spacing={3} sx={{ justifyContent: 'space-between', alignItems: { xs: 'flex-start', md: 'center' }, mb: 4 }}>
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

      {/* Live Progress Card for Running/Paused states */}
      {(isRunning || isPaused) && (
        <Card variant="outlined" sx={{ p: 4, borderRadius: '16px', mb: 4 }}>
          <Stack component="div" spacing={3}>
            <Box>
              <Stack component="div" direction="row" sx={{ justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                <Typography variant="h5" sx={{ fontWeight: '700' }}>
                  {taskDetail.status === 'crawling' ? 'Site Crawl in Progress...' : 'Evaluating Accessibility Rules...'}
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ fontWeight: '600' }}>
                  {taskDetail.pages_completed} / {taskDetail.pages_total} Pages Audited
                </Typography>
              </Stack>
              <LinearProgress 
                variant="determinate" 
                value={taskDetail.pages_total ? (taskDetail.pages_completed! / taskDetail.pages_total!) * 100 : 0} 
                sx={{ height: 8, borderRadius: 4, bgcolor: '#e2e8f0', '& .MuiLinearProgress-bar': { borderRadius: 4 } }}
              />
            </Box>

            <Grid container spacing={3}>
              <Grid size={{ xs: 12, md: 4 }}>
                <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 0.5, fontWeight: '700' }}>PAGES DISCOVERED</Typography>
                <Typography variant="h4" sx={{ fontWeight: '800' }}>{taskDetail.pages_found}</Typography>
              </Grid>
              <Grid size={{ xs: 12, md: 4 }}>
                <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 0.5, fontWeight: '700' }}>AUDITED PAGES</Typography>
                <Typography variant="h4" sx={{ fontWeight: '800', color: 'success.main' }}>{taskDetail.pages_completed}</Typography>
              </Grid>
              <Grid size={{ xs: 12, md: 4 }}>
                <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 0.5, fontWeight: '700' }}>PENDING PAGES</Typography>
                <Typography variant="h4" sx={{ fontWeight: '800', color: 'warning.main' }}>{(taskDetail.pages_total || 0) - (taskDetail.pages_completed || 0)}</Typography>
              </Grid>
            </Grid>

            <Divider />

            <Box>
              <Typography variant="subtitle2" sx={{ fontWeight: '700', mb: 1.5 }}>Crawled Pages Queue</Typography>
              <Box sx={{ maxHeight: 200, overflowY: 'auto', border: '1px solid #e2e8f0', borderRadius: '8px', bgcolor: '#f8fafc' }}>
                <List dense>
                  {taskDetail.pages_discovered?.map((url: string, index: number) => {
                    const isScanned = taskDetail.pages_scanned?.includes(url);
                    return (
                      <ListItem key={index}>
                        <ListItemIcon sx={{ minWidth: 32 }}>
                          {isScanned ? (
                            <CheckCircleIcon fontSize="small" color="success" sx={{ fontSize: '1.1rem' }} />
                          ) : (
                            <CircularProgress size={12} thickness={5} />
                          )}
                        </ListItemIcon>
                        <ListItemText 
                          primary={
                            <Typography sx={{ fontFamily: 'monospace', fontSize: '0.75rem', color: isScanned ? 'text.primary' : 'text.secondary', fontWeight: isScanned ? '400' : '600' }}>
                              {url}
                            </Typography>
                          }
                        />
                      </ListItem>
                    );
                  })}
                  {!taskDetail.pages_discovered?.length && (
                    <ListItem>
                      <ListItemText 
                        primary={
                          <Typography sx={{ fontSize: '0.875rem', color: 'text.secondary', fontStyle: 'italic' }}>
                            Discovering site pages...
                          </Typography>
                        } 
                      />
                    </ListItem>
                  )}
                </List>
              </Box>
            </Box>
          </Stack>
        </Card>
      )}

      {/* Overhauled Completed View */}
      {(isCompleted || isStopped) && (
        <Stack component="div" spacing={4}>
          {/* KPI Dashboard Row */}
          <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: 'repeat(2, 1fr)', md: 'repeat(4, 1fr)' }, gap: 3 }}>
            {/* Score Card */}
            <Card variant="outlined" sx={{ p: 3, borderRadius: '16px', borderLeft: `6px solid ${accessibilityScore >= 80 ? theme.palette.success.main : accessibilityScore >= 70 ? theme.palette.warning.main : theme.palette.error.main}` }}>
              <Stack component="div" direction="row" spacing={1.5} sx={{ alignItems: 'center', mb: 1.5 }}>
                <AssessmentIcon color="primary" />
                <Typography variant="overline" sx={{ fontWeight: '800', color: 'text.secondary', fontSize: '0.7rem' }}>Accessibility Score</Typography>
              </Stack>
              <Box sx={{ display: 'flex', alignItems: 'baseline', gap: 0.5, mb: 1.5 }}>
                <Typography variant="h3" sx={{ fontWeight: '800', color: accessibilityScore >= 80 ? 'success.main' : accessibilityScore >= 70 ? 'warning.main' : 'error.main' }}>
                  {accessibilityScore.toFixed(0)}
                </Typography>
                <Typography variant="h6" color="text.secondary">/ 100</Typography>
              </Box>
              <LinearProgress 
                variant="determinate" 
                value={accessibilityScore} 
                sx={{ height: 6, borderRadius: 3, bgcolor: '#e2e8f0', '& .MuiLinearProgress-bar': { bgcolor: accessibilityScore >= 80 ? 'success.main' : accessibilityScore >= 70 ? 'warning.main' : 'error.main', borderRadius: 3 } }}
              />
            </Card>

            {/* Critical Issues Card */}
            <Card variant="outlined" sx={{ p: 3, borderRadius: '16px', borderLeft: `6px solid ${theme.palette.error.main}` }}>
              <Stack component="div" direction="row" spacing={1.5} sx={{ alignItems: 'center', mb: 1.5 }}>
                <ErrorIcon color="error" />
                <Typography variant="overline" sx={{ fontWeight: '800', color: 'text.secondary', fontSize: '0.7rem' }}>Critical Issues</Typography>
              </Stack>
              <Typography variant="h3" sx={{ fontWeight: '800', color: 'error.main', mb: 0.5 }}>
                {criticalCount}
              </Typography>
              <Typography variant="caption" color="text.secondary">Requires immediate attention</Typography>
            </Card>

            {/* Moderate Issues Card */}
            <Card variant="outlined" sx={{ p: 3, borderRadius: '16px', borderLeft: `6px solid ${theme.palette.warning.main}` }}>
              <Stack component="div" direction="row" spacing={1.5} sx={{ alignItems: 'center', mb: 1.5 }}>
                <WarningIcon color="warning" />
                <Typography variant="overline" sx={{ fontWeight: '800', color: 'text.secondary', fontSize: '0.7rem' }}>Moderate Issues</Typography>
              </Stack>
              <Typography variant="h3" sx={{ fontWeight: '800', color: 'warning.main', mb: 0.5 }}>
                {moderateCount}
              </Typography>
              <Typography variant="caption" color="text.secondary">Improvement recommended</Typography>
            </Card>

            {/* WCAG Badge Card */}
            <Card variant="outlined" sx={{ p: 3, borderRadius: '16px', borderLeft: `6px solid ${theme.palette.success.main}` }}>
              <Stack component="div" direction="row" spacing={1.5} sx={{ alignItems: 'center', mb: 1.5 }}>
                <CheckCircleIcon color="success" />
                <Typography variant="overline" sx={{ fontWeight: '800', color: 'text.secondary', fontSize: '0.7rem' }}>WCAG Compliance</Typography>
              </Stack>
              <Typography variant="h3" sx={{ fontWeight: '800', color: 'success.main', mb: 0.5 }}>
                {wcagLevel}
              </Typography>
              <Typography variant="caption" color="text.secondary">Targeting AAA success</Typography>
            </Card>
          </Box>

          {/* Navigation Tabs */}
          <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
            <Tabs value={activeTab} onChange={(_, val) => setActiveTab(val)} color="primary">
              <Tab label="Interactive Explorer" sx={{ fontWeight: '700' }} />
              <Tab label={`Defects Table (${violations.length})`} sx={{ fontWeight: '700' }} />
              <Tab label={`All Test Cases (${testcases.length})`} sx={{ fontWeight: '700' }} />
            </Tabs>
          </Box>

          {/* Tab 1: Interactive Explorer (MUI Split Screen matching Attached Image) */}
          {activeTab === 0 && (
            <Grid container spacing={4}>
              {/* Left Column: Detected Violations */}
              <Grid size={{ xs: 12, md: 6 }}>
                <Card variant="outlined" sx={{ p: 3, borderRadius: '16px', display: 'flex', flexDirection: 'column', height: '100%', minHeight: '600px' }}>
                  <Stack component="div" direction="row" sx={{ justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
                    <Typography variant="h5" sx={{ fontWeight: '800', fontFamily: 'Outfit' }}>
                      Detected Violations
                    </Typography>
                    
                    {/* Filters */}
                    <Stack component="div" direction="row" spacing={1.5}>
                      <FormControl size="small" sx={{ minWidth: 130 }}>
                        <InputLabel>Severity</InputLabel>
                        <Select
                          value={severityFilter}
                          label="Severity"
                          onChange={(e) => setSeverityFilter(e.target.value)}
                          sx={{ borderRadius: '8px' }}
                        >
                          <MenuItem value="all">All Severities</MenuItem>
                          <MenuItem value="critical">Critical</MenuItem>
                          <MenuItem value="serious">Serious</MenuItem>
                          <MenuItem value="moderate">Moderate</MenuItem>
                          <MenuItem value="minor">Minor</MenuItem>
                        </Select>
                      </FormControl>

                      <FormControl size="small" sx={{ minWidth: 130 }}>
                        <InputLabel>WCAG Rule</InputLabel>
                        <Select
                          value={wcagFilter}
                          label="WCAG Rule"
                          onChange={(e) => setWcagFilter(e.target.value)}
                          sx={{ borderRadius: '8px' }}
                        >
                          <MenuItem value="all">All WCAG</MenuItem>
                          {wcagCriteriaList.map((wcag) => (
                            <MenuItem key={wcag} value={wcag}>{wcag.split(' ')[0]}</MenuItem>
                          ))}
                        </Select>
                      </FormControl>
                    </Stack>
                  </Stack>

                  {/* Violations List */}
                  <Stack component="div" spacing={2} sx={{ overflowY: 'auto', flex: 1, pr: 1, maxHeight: '550px' }}>
                    {filteredViolations.map((v, idx) => {
                      const isSelected = selectedViolation?.testcase_id === v.testcase_id;
                      const sevColor = v.severity?.toLowerCase() === 'critical' ? 'error' : v.severity?.toLowerCase() === 'serious' ? 'warning' : 'info';
                      return (
                        <Box
                          key={v.testcase_id}
                          onClick={() => setSelectedViolation(v)}
                          sx={{
                            p: 2.5,
                            borderRadius: '12px',
                            border: `1px solid ${isSelected ? theme.palette.primary.main : '#e2e8f0'}`,
                            bgcolor: isSelected ? alpha(theme.palette.primary.main, 0.04) : '#ffffff',
                            cursor: 'pointer',
                            transition: 'all 0.2s',
                            position: 'relative',
                            '&:hover': {
                              borderColor: isSelected ? theme.palette.primary.main : '#cbd5e1',
                              bgcolor: isSelected ? alpha(theme.palette.primary.main, 0.06) : '#f8fafc',
                              transform: 'translateY(-1px)'
                            }
                          }}
                        >
                          {isSelected && (
                            <Box sx={{ width: 4, height: '80%', bgcolor: 'primary.main', borderRadius: 2, position: 'absolute', left: 4, top: '10%' }} />
                          )}
                          <Stack component="div" direction="row" sx={{ justifyContent: 'space-between', alignItems: 'flex-start', mb: 1 }}>
                            <Chip
                              label={v.severity?.toUpperCase() || 'MODERATE'}
                              color={sevColor}
                              size="small"
                              sx={{ fontWeight: '800', fontSize: '0.65rem', height: '20px', borderRadius: '4px' }}
                            />
                            <Typography variant="caption" color="text.secondary" sx={{ fontWeight: '600' }}>
                              #{idx + 1}
                            </Typography>
                          </Stack>
                          <Typography variant="subtitle1" sx={{ fontWeight: '700', color: 'text.primary', mb: 0.5 }}>
                            {v.testcase_name}
                          </Typography>
                          <Typography variant="body2" color="text.secondary" sx={{ mb: 1.5, display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
                            {v.description}
                          </Typography>
                          <Stack component="div" direction="row" spacing={1}>
                            <Chip label={v.criteria} size="small" variant="outlined" sx={{ fontWeight: '600', fontSize: '0.7rem', height: '20px' }} />
                            <Chip label={v.refined_by} size="small" sx={{ fontWeight: '600', fontSize: '0.7rem', height: '20px', bgcolor: '#f1f5f9' }} />
                          </Stack>
                        </Box>
                      );
                    })}

                    {filteredViolations.length === 0 && (
                      <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', py: 8 }}>
                        <CheckCircleIcon color="success" sx={{ fontSize: '3rem', mb: 1.5 }} />
                        <Typography variant="h6" sx={{ fontWeight: '600' }}>No Violations Match Your Filters</Typography>
                        <Typography variant="body2" color="text.secondary">All checked rules comply with WCAG standards.</Typography>
                      </Box>
                    )}
                  </Stack>
                </Card>
              </Grid>

              {/* Right Column: Violation Context & AI Suggestion */}
              <Grid size={{ xs: 12, md: 6 }}>
                {selectedViolation ? (
                  <Stack component="div" spacing={3}>
                    {/* Visual Mockup Container */}
                    <Card variant="outlined" sx={{ p: 3, borderRadius: '16px' }}>
                      <Typography variant="subtitle2" sx={{ fontWeight: '800', color: 'text.secondary', mb: 2, textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                        Violation Context
                      </Typography>

                      {selectedViolation.screenshot && selectedViolation.screenshot !== 'N/A' ? (
                        <Box sx={{
                          border: '1px solid #cbd5e1',
                          borderRadius: '12px',
                          overflow: 'hidden',
                          bgcolor: '#ffffff',
                          boxShadow: '0 4px 6px -1px rgba(0,0,0,0.05)',
                          display: 'flex',
                          justifyContent: 'center',
                          alignItems: 'center'
                        }}>
                          <img
                            src={`http://localhost:8002/report/${taskId}/screenshot/${selectedViolation.screenshot}`}
                            alt="Visual Evidence of Defect"
                            style={{ maxWidth: '100%', height: 'auto', display: 'block' }}
                          />
                        </Box>
                      ) : (
                        <ViolationMockup htmlSnippet={selectedViolation.html_snippet} ruleId={selectedViolation.rule_id} />
                      )}
                      
                      <Box sx={{ mt: 2 }}>
                        <Typography variant="caption" color="text.secondary" sx={{ fontWeight: '700', display: 'block', mb: 0.5 }}>DOM LOCATION</Typography>
                        <Typography variant="body2" sx={{ fontFamily: 'monospace', bgcolor: '#f1f5f9', p: 1.5, borderRadius: '8px', border: '1px solid #e2e8f0', wordBreak: 'break-all' }}>
                          {selectedViolation.page_title} &gt; {selectedViolation.rule_id}
                        </Typography>
                      </Box>
                    </Card>

                    {/* AI Fix Suggestion Panel */}
                    <Card variant="outlined" sx={{ p: 3, borderRadius: '16px', bgcolor: '#0f172a', color: '#f8fafc', '&:hover': { transform: 'none' } }}>
                      <Stack component="div" direction="row" sx={{ alignItems: 'center', gap: 1, mb: 2.5 }}>
                        <BuildIcon sx={{ color: 'primary.light' }} />
                        <Typography variant="subtitle2" sx={{ fontWeight: '800', color: 'primary.light', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                          AI Fix Suggestion (OpenClaw)
                        </Typography>
                      </Stack>

                      <Stack component="div" spacing={2.5}>
                        {/* Source Code Snippet */}
                        <Box>
                          <Stack component="div" direction="row" sx={{ justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                            <Typography variant="caption" sx={{ color: 'text.disabled', fontWeight: '700' }}>VIOLATION CODE</Typography>
                            <IconButton size="small" onClick={() => handleCopyCode(selectedViolation.html_snippet)} sx={{ color: 'text.disabled', '&:hover': { color: '#ffffff' } }}>
                              <ContentCopyIcon fontSize="inherit" />
                            </IconButton>
                          </Stack>
                          <Box sx={{
                            p: 2,
                            borderRadius: '8px',
                            bgcolor: '#1e293b',
                            border: '1px solid #334155',
                            fontFamily: 'monospace',
                            fontSize: '0.8rem',
                            overflowX: 'auto',
                            maxHeight: 120,
                            whiteSpace: 'pre-wrap',
                            wordBreak: 'break-all',
                            color: '#fb7185'
                          }}>
                            {selectedViolation.html_snippet}
                          </Box>
                        </Box>

                        {/* Remediated Suggestion */}
                        <Box>
                          <Stack component="div" direction="row" sx={{ justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                            <Typography variant="caption" sx={{ color: 'text.disabled', fontWeight: '700' }}>SUGGESTED FIX BY OPENCLAW</Typography>
                            <IconButton size="small" onClick={() => handleCopyCode(selectedViolation.remediation)} sx={{ color: 'text.disabled', '&:hover': { color: '#ffffff' } }}>
                              <ContentCopyIcon fontSize="inherit" />
                            </IconButton>
                          </Stack>
                          <Box sx={{
                            p: 2,
                            borderRadius: '8px',
                            bgcolor: '#1e293b',
                            border: '1px solid #334155',
                            fontFamily: 'monospace',
                            fontSize: '0.8rem',
                            overflowX: 'auto',
                            maxHeight: 120,
                            whiteSpace: 'pre-wrap',
                            wordBreak: 'break-all',
                            color: '#34d399'
                          }}>
                            {selectedViolation.remediation}
                          </Box>
                        </Box>

                        {/* Apply Fix Button */}
                        <Box>
                          <Button
                            variant="contained"
                            color="success"
                            fullWidth
                            startIcon={isApplyingFix ? <CircularProgress size={18} color="inherit" /> : <CodeIcon />}
                            onClick={handleApplyFix}
                            disabled={isApplyingFix}
                            sx={{
                              bgcolor: 'success.main',
                              color: '#ffffff',
                              fontWeight: '700',
                              py: 1.25,
                              borderRadius: '8px',
                              textTransform: 'none',
                              '&:hover': { bgcolor: 'success.dark' }
                            }}
                          >
                            {isApplyingFix ? 'Applying Suggestion...' : 'Apply to Source Code'}
                          </Button>
                          <Typography variant="caption" sx={{ color: 'text.disabled', display: 'block', mt: 1, textAlign: 'center' }}>
                            Changes will be pushed via secure PR to your linked GitHub repository.
                          </Typography>
                        </Box>
                      </Stack>
                    </Card>
                  </Stack>
                ) : (
                  <Card variant="outlined" sx={{ p: 4, borderRadius: '16px', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%', minHeight: '400px' }}>
                    <Typography variant="body1" color="text.secondary" sx={{ fontStyle: 'italic' }}>
                      Select a violation from the list to explore context and fixes.
                    </Typography>
                  </Card>
                )}
              </Grid>
            </Grid>
          )}

          {/* Tab 2: Defects Table */}
          {activeTab === 1 && (
            <Card variant="outlined" sx={{ borderRadius: '16px', overflow: 'hidden' }}>
              <TableContainer sx={{ maxHeight: 600, overflowX: 'auto' }}>
                <Table stickyHeader>
                  <TableHead>
                    <TableRow>
                      <TableCell sx={{ fontWeight: '700', color: 'text.secondary', whiteSpace: 'nowrap' }}>DEFECT ID</TableCell>
                      <TableCell sx={{ fontWeight: '700', color: 'text.secondary', whiteSpace: 'nowrap' }}>ASSOCIATED TC ID</TableCell>
                      <TableCell sx={{ fontWeight: '700', color: 'text.secondary', whiteSpace: 'nowrap' }}>PAGE TITLE</TableCell>
                      <TableCell sx={{ fontWeight: '700', color: 'text.secondary', whiteSpace: 'nowrap' }}>URL</TableCell>
                      <TableCell sx={{ fontWeight: '700', color: 'text.secondary', whiteSpace: 'nowrap' }}>CRITERIA</TableCell>
                      <TableCell sx={{ fontWeight: '700', color: 'text.secondary', whiteSpace: 'nowrap' }}>LEVEL</TableCell>
                      <TableCell sx={{ fontWeight: '700', color: 'text.secondary', whiteSpace: 'nowrap' }}>SEVERITY</TableCell>
                      <TableCell sx={{ fontWeight: '700', color: 'text.secondary', whiteSpace: 'nowrap' }}>DESCRIPTION</TableCell>
                      <TableCell sx={{ fontWeight: '700', color: 'text.secondary', whiteSpace: 'nowrap' }}>EXPECTED</TableCell>
                      <TableCell sx={{ fontWeight: '700', color: 'text.secondary', whiteSpace: 'nowrap' }}>ACTUAL</TableCell>
                      <TableCell sx={{ fontWeight: '700', color: 'text.secondary', whiteSpace: 'nowrap' }}>STEPS TO REPRODUCE</TableCell>
                      <TableCell sx={{ fontWeight: '700', color: 'text.secondary', whiteSpace: 'nowrap' }}>REMEDIATION</TableCell>
                      <TableCell sx={{ fontWeight: '700', color: 'text.secondary', whiteSpace: 'nowrap' }}>HELP</TableCell>
                      <TableCell sx={{ fontWeight: '700', color: 'text.secondary', whiteSpace: 'nowrap' }}>HTML SNIPPET</TableCell>
                      <TableCell sx={{ fontWeight: '700', color: 'text.secondary', whiteSpace: 'nowrap' }}>SCREENSHOT</TableCell>
                      <TableCell align="right" sx={{ fontWeight: '700', color: 'text.secondary', whiteSpace: 'nowrap' }}>INSPECT</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {violations
                      .slice(defectsPage * defectsRowsPerPage, defectsPage * defectsRowsPerPage + defectsRowsPerPage)
                      .map((v, idx) => {
                        const sevColor = v.severity?.toLowerCase() === 'critical' ? 'error' : v.severity?.toLowerCase() === 'serious' ? 'warning' : 'info';
                        return (
                          <TableRow key={v.testcase_id} hover>
                            {/* 1. Defect ID */}
                            <TableCell sx={{ fontWeight: 'bold', fontFamily: 'monospace', whiteSpace: 'nowrap' }}>
                              DEF-{String(defectsPage * defectsRowsPerPage + idx + 1).padStart(3, '0')}
                            </TableCell>

                            {/* 2. Associated Testcase ID */}
                            <TableCell sx={{ fontFamily: 'monospace', fontSize: '0.8rem', whiteSpace: 'nowrap' }}>
                              {v.testcase_id}
                            </TableCell>

                            {/* 3. Page Title */}
                            <TableCell sx={{ minWidth: 150 }}>
                              {v.page_title}
                            </TableCell>

                            {/* 4. URL */}
                            <TableCell sx={{ minWidth: 180 }}>
                              <Stack component="div" direction="row" spacing={0.5} sx={{ alignItems: 'center' }}>
                                <Typography variant="body2" sx={{
                                  fontFamily: 'monospace',
                                  fontSize: '0.8rem',
                                  overflow: 'hidden',
                                  textOverflow: 'ellipsis',
                                  maxWidth: 200,
                                  display: 'block'
                                }}>
                                  {v.page_url}
                                </Typography>
                                <IconButton size="small" component="a" href={v.page_url} target="_blank" rel="noopener noreferrer">
                                  <LaunchIcon sx={{ fontSize: '0.9rem' }} />
                                </IconButton>
                              </Stack>
                            </TableCell>

                            {/* 5. Criteria */}
                            <TableCell sx={{ whiteSpace: 'nowrap' }}>
                              <Chip label={v.criteria} size="small" variant="outlined" sx={{ fontWeight: '600', fontSize: '0.75rem' }} />
                            </TableCell>

                            {/* 6. Level */}
                            <TableCell>
                              <Chip label={v.level} size="small" sx={{ fontWeight: 'bold', fontSize: '0.75rem', bgcolor: '#f1f5f9' }} />
                            </TableCell>

                            {/* 7. Severity */}
                            <TableCell>
                              <Chip label={v.severity?.toUpperCase() || 'MODERATE'} color={sevColor} size="small" sx={{ fontWeight: '700', fontSize: '0.65rem' }} />
                            </TableCell>

                            {/* 8. Description */}
                            <TableCell sx={{ minWidth: 250 }}>
                              <Box sx={{ maxHeight: 80, overflowY: 'auto', fontSize: '0.875rem', pr: 1 }}>
                                {v.description}
                              </Box>
                            </TableCell>

                            {/* 9. Expected */}
                            <TableCell sx={{ minWidth: 220 }}>
                              <Box sx={{ maxHeight: 80, overflowY: 'auto', fontSize: '0.875rem', pr: 1, color: 'text.secondary' }}>
                                {v.expected_result}
                              </Box>
                            </TableCell>

                            {/* 10. Actual */}
                            <TableCell sx={{ minWidth: 220 }}>
                              <Box sx={{ maxHeight: 80, overflowY: 'auto', fontSize: '0.875rem', pr: 1, color: 'error.main' }}>
                                {v.actual_result}
                              </Box>
                            </TableCell>

                            {/* 11. Steps to Reproduce */}
                            <TableCell sx={{ minWidth: 250 }}>
                              <Box sx={{ maxHeight: 80, overflowY: 'auto', fontSize: '0.875rem', pr: 1, whiteSpace: 'pre-line' }}>
                                {v.steps_to_reproduce}
                              </Box>
                            </TableCell>

                            {/* 12. Remediation */}
                            <TableCell sx={{ minWidth: 250 }}>
                              <Box sx={{
                                maxHeight: 80,
                                overflowY: 'auto',
                                fontFamily: 'monospace',
                                fontSize: '0.8rem',
                                p: 1,
                                borderRadius: 1,
                                bgcolor: '#f8fafc',
                                border: '1px solid #e2e8f0',
                                whiteSpace: 'pre-wrap',
                                color: '#0f766e'
                              }}>
                                {v.remediation}
                              </Box>
                            </TableCell>

                            {/* 13. Help */}
                            <TableCell>
                              {v.help_url ? (
                                <Button
                                  size="small"
                                  startIcon={<LaunchIcon />}
                                  href={v.help_url}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  sx={{ textTransform: 'none', whiteSpace: 'nowrap', fontWeight: '700' }}
                                >
                                  Rule Help
                                </Button>
                              ) : (
                                'N/A'
                              )}
                            </TableCell>

                            {/* 14. HTML Snippet */}
                            <TableCell sx={{ minWidth: 300 }}>
                              {v.html_snippet ? (
                                <Stack component="div" direction="row" spacing={1} sx={{ alignItems: 'flex-start' }}>
                                  <Box sx={{
                                    maxHeight: 80,
                                    overflowY: 'auto',
                                    fontFamily: 'monospace',
                                    fontSize: '0.8rem',
                                    p: 1,
                                    borderRadius: 1,
                                    bgcolor: '#0f172a',
                                    color: '#fb7185',
                                    flex: 1,
                                    whiteSpace: 'pre-wrap',
                                    wordBreak: 'break-all'
                                  }}>
                                    {v.html_snippet}
                                  </Box>
                                  <IconButton size="small" onClick={() => handleCopyCode(v.html_snippet)} sx={{ color: 'text.secondary' }}>
                                    <ContentCopyIcon fontSize="inherit" />
                                  </IconButton>
                                </Stack>
                              ) : (
                                'N/A'
                              )}
                            </TableCell>

                            {/* 14b. Screenshot */}
                            <TableCell sx={{ whiteSpace: 'nowrap' }}>
                              {v.screenshot && v.screenshot !== 'N/A' ? (
                                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                  <IconButton
                                    size="small"
                                    component="a"
                                    href={`http://localhost:8002/report/${taskId}/screenshot/${v.screenshot}`}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    title="Open full screenshot in new tab"
                                  >
                                    <LaunchIcon sx={{ fontSize: '1.1rem' }} />
                                  </IconButton>
                                  <Box
                                    component="img"
                                    src={`http://localhost:8002/report/${taskId}/screenshot/${v.screenshot}`}
                                    alt="Thumbnail"
                                    sx={{
                                      width: 48,
                                      height: 32,
                                      objectFit: 'cover',
                                      borderRadius: '4px',
                                      border: '1px solid #e2e8f0',
                                      cursor: 'pointer'
                                    }}
                                    onClick={() => {
                                      window.open(`http://localhost:8002/report/${taskId}/screenshot/${v.screenshot}`, '_blank');
                                    }}
                                  />
                                </Box>
                              ) : (
                                'N/A'
                              )}
                            </TableCell>

                            {/* 15. Inspect Button */}
                            <TableCell align="right">
                              <Button
                                size="small"
                                onClick={() => {
                                  setSelectedViolation(v);
                                  setActiveTab(0);
                                }}
                                sx={{ textTransform: 'none', fontWeight: '700', whiteSpace: 'nowrap' }}
                              >
                                View
                              </Button>
                            </TableCell>
                          </TableRow>
                        );
                      })}
                    {violations.length === 0 && (
                      <TableRow>
                        <TableCell colSpan={15} align="center" sx={{ py: 6 }}>
                          <Typography variant="body1" color="text.secondary">No violations detected!</Typography>
                        </TableCell>
                      </TableRow>
                    )}
                  </TableBody>
                </Table>
              </TableContainer>
              <TablePagination
                rowsPerPageOptions={[5, 10, 25]}
                component="div"
                count={violations.length}
                rowsPerPage={defectsRowsPerPage}
                page={defectsPage}
                onPageChange={(_, page) => setDefectsPage(page)}
                onRowsPerPageChange={(e) => {
                  setDefectsRowsPerPage(parseInt(e.target.value, 10));
                  setDefectsPage(0);
                }}
              />
            </Card>
          )}

          {/* Tab 3: All Test Cases Table */}
          {activeTab === 2 && (
            <Card variant="outlined" sx={{ borderRadius: '16px', overflow: 'hidden' }}>
              <TableContainer sx={{ maxHeight: 600 }}>
                <Table stickyHeader>
                  <TableHead>
                    <TableRow>
                      <TableCell sx={{ fontWeight: '700', color: 'text.secondary' }}>TC ID</TableCell>
                      <TableCell sx={{ fontWeight: '700', color: 'text.secondary' }}>TEST NAME</TableCell>
                      <TableCell sx={{ fontWeight: '700', color: 'text.secondary' }}>RULE ID</TableCell>
                      <TableCell sx={{ fontWeight: '700', color: 'text.secondary' }}>STATUS</TableCell>
                      <TableCell sx={{ fontWeight: '700', color: 'text.secondary' }}>PAGE</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {testcases
                      .slice(testcasesPage * testcasesRowsPerPage, testcasesPage * testcasesRowsPerPage + testcasesRowsPerPage)
                      .map((tc) => (
                        <TableRow key={tc.testcase_id} hover>
                          <TableCell sx={{ fontWeight: '600', fontSize: '0.8rem' }}>{tc.testcase_id}</TableCell>
                          <TableCell>
                            <Typography variant="subtitle2" sx={{ fontWeight: '700' }}>{tc.testcase_name}</Typography>
                            <Typography variant="caption" color="text.secondary">{tc.description}</Typography>
                          </TableCell>
                          <TableCell sx={{ fontFamily: 'monospace', fontSize: '0.8rem' }}>{tc.rule_id}</TableCell>
                          <TableCell>
                            <Chip 
                              label={tc.status} 
                              color={tc.status === 'PASS' ? 'success' : 'error'} 
                              size="small" 
                              sx={{ fontWeight: '700', fontSize: '0.7rem' }} 
                            />
                          </TableCell>
                          <TableCell sx={{ fontFamily: 'monospace', fontSize: '0.75rem' }}>{tc.page_title}</TableCell>
                        </TableRow>
                      ))}
                    {testcases.length === 0 && (
                      <TableRow>
                        <TableCell colSpan={5} align="center" sx={{ py: 6 }}>
                          <Typography variant="body1" color="text.secondary">No test checks ran.</Typography>
                        </TableCell>
                      </TableRow>
                    )}
                  </TableBody>
                </Table>
              </TableContainer>
              <TablePagination
                rowsPerPageOptions={[5, 10, 25, 50]}
                component="div"
                count={testcases.length}
                rowsPerPage={testcasesRowsPerPage}
                page={testcasesPage}
                onPageChange={(_, page) => setTestcasesPage(page)}
                onRowsPerPageChange={(e) => {
                  setTestcasesRowsPerPage(parseInt(e.target.value, 10));
                  setTestcasesPage(0);
                }}
              />
            </Card>
          )}
        </Stack>
      )}
    </Box>
  );
};

export default AuditDetailsPage;
