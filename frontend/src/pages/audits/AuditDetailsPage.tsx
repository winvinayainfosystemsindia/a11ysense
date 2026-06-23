import React from 'react';
import {
  Box,
  Typography,
  Button,
  CircularProgress,
  Tabs,
  Tab,
  Stack
} from '@mui/material';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import { useAuditDetails } from '../../components/audits/hooks/useAuditDetails';

// Child components
import { AuditHeader } from '../../components/audits/details/AuditHeader';
import { AuditLiveProgress } from '../../components/audits/details/AuditLiveProgress';
import { CompletedViewDashboard } from '../../components/audits/details/CompletedViewDashboard';
import { InteractiveExplorerTab } from '../../components/audits/details/InteractiveExplorerTab';
import { TestCasesTableTab } from '../../components/audits/details/TestCasesTableTab';
import { DefectsTableTab } from '../../components/audits/details/DefectsTableTab';
import { UrlsListTab } from '../../components/audits/details/UrlsListTab';

const AuditDetailsPage: React.FC = () => {
  const {
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
  } = useAuditDetails();

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

  return (
    <Box sx={{ pb: 6 }}>
      <Button startIcon={<ArrowBackIcon />} onClick={handleBack} sx={{ mb: 3 }}>
        Back to Audits
      </Button>

      {/* Header Panel */}
      <AuditHeader
        taskId={taskId}
        taskDetail={taskDetail}
        isCompleted={isCompleted}
        isStopped={isStopped}
        isRunning={isRunning}
        isPaused={isPaused}
        actionLoading={actionLoading}
        handleOpenReport={handleOpenReport}
        handleExportReport={handleExportReport}
        handlePause={handlePause}
        handleResume={handleResume}
        handleStop={handleStop}
      />

      {/* Live Progress Card for Running/Paused states */}
      {(isRunning || isPaused) && (
        <AuditLiveProgress taskDetail={taskDetail} />
      )}

      {/* Completed View */}
      {(isCompleted || isStopped) && (
        <Stack component="div" spacing={4}>
          <CompletedViewDashboard
            accessibilityScore={accessibilityScore}
            criticalCount={criticalCount}
            totalIssuesCount={totalIssuesCount}
            pagesScannedCount={pagesScannedCount}
            pagesDiscoveredCount={pagesDiscoveredCount}
          />

          {/* Navigation Tabs */}
          <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
            <Tabs value={activeTab} onChange={(_, val) => setActiveTab(val)} color="primary">
              <Tab label="Explorer" sx={{ fontWeight: '700' }} />
              <Tab label={`Test Case (${testcases.length})`} sx={{ fontWeight: '700' }} />
              <Tab label={`Defects Table (${violations.length})`} sx={{ fontWeight: '700' }} />
              <Tab label={`List of URLs (${taskDetail.pages_discovered?.length || 0})`} sx={{ fontWeight: '700' }} />
            </Tabs>
          </Box>

          {/* Tab 1: Interactive Explorer */}
          {activeTab === 0 && (
            <InteractiveExplorerTab
              taskId={taskId}
              filteredViolations={filteredViolations}
              selectedViolation={selectedViolation}
              setSelectedViolation={setSelectedViolation}
              severityFilter={severityFilter}
              setSeverityFilter={setSeverityFilter}
              wcagFilter={wcagFilter}
              setWcagFilter={setWcagFilter}
              wcagCriteriaList={wcagCriteriaList}
              isApplyingFix={isApplyingFix}
              handleApplyFix={handleApplyFix}
              handleCopyCode={handleCopyCode}
            />
          )}

          {/* Tab 2: Test Case Table */}
          {activeTab === 1 && (
            <TestCasesTableTab
              testcases={testcases}
              testcasesPage={testcasesPage}
              setTestcasesPage={setTestcasesPage}
              testcasesRowsPerPage={testcasesRowsPerPage}
              setTestcasesRowsPerPage={setTestcasesRowsPerPage}
            />
          )}

          {/* Tab 3: Defects Table */}
          {activeTab === 2 && (
            <DefectsTableTab
              violations={violations}
              defectsPage={defectsPage}
              setDefectsPage={setDefectsPage}
              defectsRowsPerPage={defectsRowsPerPage}
              setDefectsRowsPerPage={setDefectsRowsPerPage}
              taskId={taskId}
              handleCopyCode={handleCopyCode}
              setSelectedViolation={setSelectedViolation}
              setActiveTab={setActiveTab}
            />
          )}

          {/* Tab 4: List of URLs */}
          {activeTab === 3 && (
            <UrlsListTab
              taskDetail={taskDetail}
              urlSearchQuery={urlSearchQuery}
              setUrlSearchQuery={setUrlSearchQuery}
              filteredDiscoveredUrls={filteredDiscoveredUrls}
              urlsPage={urlsPage}
              setUrlsPage={setUrlsPage}
              urlsRowsPerPage={urlsRowsPerPage}
              setUrlsRowsPerPage={setUrlsRowsPerPage}
            />
          )}
        </Stack>
      )}
    </Box>
  );
};

export default AuditDetailsPage;

