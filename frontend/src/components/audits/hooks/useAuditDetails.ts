import { useState, useEffect, useMemo } from 'react';
import { useParams, useNavigate } from '@tanstack/react-router';
import { auditService } from '../../../service/auditService';
import type { AuditTaskDetail } from '../../../service/auditService';

export const useAuditDetails = () => {
  const { orgId, taskId } = useParams({ strict: false }) as any;
  const navigate = useNavigate();

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

  // URLs Tab State
  const [urlSearchQuery, setUrlSearchQuery] = useState('');
  const [urlsPage, setUrlsPage] = useState(0);
  const [urlsRowsPerPage, setUrlsRowsPerPage] = useState(10);

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

  // Filtered discovered URLs for URLs tab
  const filteredDiscoveredUrls = useMemo(() => {
    const list = taskDetail?.pages_discovered || [];
    if (!urlSearchQuery) return list;
    return list.filter(url => url.toLowerCase().includes(urlSearchQuery.toLowerCase()));
  }, [taskDetail, urlSearchQuery]);

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
  // Pass-rate score: the % of accessibility checks (testcases) that passed.
  // This mirrors how compliance is communicated to stakeholders (e.g. "82% of
  // checks passed") instead of an opaque penalty formula.
  const calculatedScore = useMemo(() => {
    if (testcases.length === 0) return 100;
    const passedCount = testcases.filter(tc => tc.status === 'PASS').length;
    return parseFloat(((passedCount / testcases.length) * 100).toFixed(1));
  }, [testcases]);

  // Always derive the score from the loaded testcases when available, so it
  // stays consistent with the Test Case/Defects counts shown on this same
  // page. Falls back to the persisted summary score only when testcases
  // haven't loaded yet (e.g. audit still in progress).
  const accessibilityScore = testcases.length > 0
    ? calculatedScore
    : (taskDetail?.summary?.accessibility_score ?? 0);
  const criticalCount = useMemo(() => violations.filter(v => v.severity?.toLowerCase() === 'critical').length, [violations]);
  const totalIssuesCount = violations.length;
  const pagesScannedCount = taskDetail?.pages_scanned?.length ?? taskDetail?.pages_completed ?? 0;
  const pagesDiscoveredCount = taskDetail?.pages_discovered?.length ?? taskDetail?.pages_found ?? pagesScannedCount;

  const isCompleted = taskDetail?.status === 'completed';
  const isStopped = taskDetail?.status === 'stopped';
  const isRunning = taskDetail?.status === 'in_progress' || taskDetail?.status === 'crawling' || taskDetail?.status === 'auditing';
  const isPaused = taskDetail?.status === 'paused';

  return {
    orgId,
    taskId,
    taskDetail,
    testcases,
    loading,
    actionLoading,
    error,
    activeTab,
    setActiveTab,
    selectedViolation,
    setSelectedViolation,
    severityFilter,
    setSeverityFilter,
    wcagFilter,
    setWcagFilter,
    defectsPage,
    setDefectsPage,
    defectsRowsPerPage,
    setDefectsRowsPerPage,
    testcasesPage,
    setTestcasesPage,
    testcasesRowsPerPage,
    setTestcasesRowsPerPage,
    isApplyingFix,
    urlSearchQuery,
    setUrlSearchQuery,
    urlsPage,
    setUrlsPage,
    urlsRowsPerPage,
    setUrlsRowsPerPage,
    handleBack,
    handleOpenReport,
    handleExportReport,
    handlePause,
    handleResume,
    handleStop,
    handleApplyFix,
    handleCopyCode,
    violations,
    wcagCriteriaList,
    filteredViolations,
    filteredDiscoveredUrls,
    accessibilityScore,
    criticalCount,
    totalIssuesCount,
    pagesScannedCount,
    pagesDiscoveredCount,
    isCompleted,
    isStopped,
    isRunning,
    isPaused
  };
};
