import React, { useState } from 'react';
import {
  Box,
  Typography,
  Stack,
  Button,
  Card,
  CircularProgress,
  Alert,
  useTheme,
} from '@mui/material';
import { alpha } from '@mui/material/styles';
import FileDownloadIcon from '@mui/icons-material/FileDownload';
import DescriptionIcon from '@mui/icons-material/Description';
import PrintIcon from '@mui/icons-material/Print';

import { estimationService } from '../../service/estimationService';
import type {
  EstimationResult,
  EstimatedPage,
  DiscoveredUrlItem,
} from '../../service/estimationService';

import {
  ComplexityMatrixGuide,
  EstimationUrlInputCard,
  CommercialRateConfigurator,
  EstimationKpiCards,
  ComplexityDistributionCard,
  EstimationLineItemsTable,
} from '../../components/estimation';

export const EstimationPage: React.FC = () => {
  const theme = useTheme();

  // Mode selection: 0 = "Discover from Base URL", 1 = "Direct URL List"
  const [inputMode, setInputMode] = useState<number>(0);

  // Mode 0: Discover from Base URL
  const [baseUrl, setBaseUrl] = useState('');
  const [discoveryDepth, setDiscoveryDepth] = useState<number>(1);
  const [maxDiscovery, setMaxDiscovery] = useState<number>(30);
  const [discovering, setDiscovering] = useState(false);
  const [discoveredPages, setDiscoveredPages] = useState<DiscoveredUrlItem[]>([]);
  const [selectedUrls, setSelectedUrls] = useState<Record<string, boolean>>({});
  const [filterKeyword, setFilterKeyword] = useState('');

  // Mode 1: Direct Custom URL list
  const [customUrlsText, setCustomUrlsText] = useState('');

  // Commercial rate adjusters
  const [hourlyRate, setHourlyRate] = useState<number>(40);
  const [platformFee, setPlatformFee] = useState<number>(10);
  const [profitMarginPct, setProfitMarginPct] = useState<number>(30);

  // Analysis execution & results
  const [analyzing, setAnalyzing] = useState(false);
  const [exportingExcel, setExportingExcel] = useState(false);
  const [exportingPdf, setExportingPdf] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<EstimationResult | null>(null);
  const [expandedRows, setExpandedRows] = useState<Record<number, boolean>>({});
  const [showCriteriaGuide, setShowCriteriaGuide] = useState(false);

  // Helper for custom URLs parsing
  const getParsedCustomUrls = (): string[] => {
    return customUrlsText
      .split(/[\n,]+/)
      .map((u) => u.trim())
      .filter((u) => u.length > 0);
  };

  // Discover URLs from Base URL
  const handleDiscover = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!baseUrl.trim()) return;

    setDiscovering(true);
    setError(null);
    try {
      const data = await estimationService.discover({
        url: baseUrl.trim(),
        depth: discoveryDepth,
        max_pages: maxDiscovery,
      });
      setDiscoveredPages(data.urls);
      // Select all discovered URLs by default
      const initialSelected: Record<string, boolean> = {};
      data.urls.forEach((item) => {
        initialSelected[item.url] = true;
      });
      setSelectedUrls(initialSelected);
    } catch (err: any) {
      console.error('URL discovery failed:', err);
      setError(err?.response?.data?.detail || err?.message || 'Failed to discover website URLs.');
    } finally {
      setDiscovering(false);
    }
  };

  const handleToggleUrl = (targetUrl: string) => {
    setSelectedUrls((prev) => ({
      ...prev,
      [targetUrl]: !prev[targetUrl],
    }));
  };

  const handleSelectAll = () => {
    const updated: Record<string, boolean> = {};
    discoveredPages.forEach((p) => {
      updated[p.url] = true;
    });
    setSelectedUrls(updated);
  };

  const handleDeselectAll = () => {
    setSelectedUrls({});
  };

  // Run Estimation Analysis
  const handleAnalyzeSelected = async () => {
    let targetUrls: string[] = [];

    if (inputMode === 0) {
      targetUrls = Object.entries(selectedUrls)
        .filter(([_, isSelected]) => isSelected)
        .map(([url]) => url);
      if (targetUrls.length === 0) {
        setError('Please select at least one discovered URL to evaluate.');
        return;
      }
    } else {
      targetUrls = getParsedCustomUrls();
      if (targetUrls.length === 0) {
        setError('Please enter at least one valid URL in the text area.');
        return;
      }
    }

    setAnalyzing(true);
    setError(null);
    try {
      const data = await estimationService.analyze({
        urls: targetUrls,
        hourly_rate: hourlyRate,
        platform_fee: platformFee,
        profit_margin_pct: profitMarginPct,
      });
      setResult(data);
    } catch (err: any) {
      console.error('Estimation failed:', err);
      setError(err?.response?.data?.detail || err?.message || 'Failed to calculate estimation.');
    } finally {
      setAnalyzing(false);
    }
  };

  // Recalculate with modified rates or manual tier adjustments
  const handleRecalculate = async (
    hRate: number,
    pFee: number,
    marginPct: number,
    updatedPages?: EstimatedPage[]
  ) => {
    const pagesToRecalc = updatedPages || result?.pages;
    if (!pagesToRecalc || pagesToRecalc.length === 0) return;

    try {
      const updated = await estimationService.recalculate({
        pages: pagesToRecalc,
        hourly_rate: hRate,
        platform_fee: pFee,
        profit_margin_pct: marginPct,
      });
      setResult(updated);
    } catch (err: any) {
      console.error('Recalculation error:', err);
    }
  };

  const handleRateConfigurationChange = (
    newHourlyRate: number,
    newPlatformFee: number,
    newProfitMarginPct: number
  ) => {
    setHourlyRate(newHourlyRate);
    setPlatformFee(newPlatformFee);
    setProfitMarginPct(newProfitMarginPct);
    handleRecalculate(newHourlyRate, newPlatformFee, newProfitMarginPct);
  };

  // Allow auditor to manually override a page's complexity tier
  const handlePageComplexityOverride = (
    pageIndex: number,
    newComplexity: 'simple' | 'medium' | 'complex'
  ) => {
    if (!result) return;
    const updatedPages = [...result.pages];
    const targetPage = { ...updatedPages[pageIndex] };
    targetPage.complexity = newComplexity;
    targetPage.complexity_label =
      newComplexity === 'simple' ? 'Simple' : newComplexity === 'medium' ? 'Medium' : 'Complex';

    // Update rationale note
    targetPage.summary_rationale = `Manual auditor override applied: Set to ${targetPage.complexity_label}.`;
    targetPage.triggers = [`Auditor override: ${targetPage.complexity_label} tier`];
    updatedPages[pageIndex] = targetPage;

    handleRecalculate(hourlyRate, platformFee, profitMarginPct, updatedPages);
  };

  // Download Commercial Excel (.xlsx)
  const handleDownloadExcel = async () => {
    if (!result) return;
    setExportingExcel(true);
    try {
      await estimationService.downloadQuotationExcel(result);
    } catch (err: any) {
      console.error('Failed to download Excel proposal:', err);
      setError('Failed to download Excel quotation.');
    } finally {
      setExportingExcel(false);
    }
  };

  // Download Formal PDF (.pdf)
  const handleDownloadPdf = async () => {
    if (!result) return;
    setExportingPdf(true);
    try {
      await estimationService.downloadQuotationPdf(result);
    } catch (err: any) {
      console.error('Failed to download PDF proposal:', err);
      setError('Failed to download PDF proposal.');
    } finally {
      setExportingPdf(false);
    }
  };

  const toggleRow = (idx: number) => {
    setExpandedRows((prev) => ({
      ...prev,
      [idx]: !prev[idx],
    }));
  };

  return (
    <Box sx={{ pb: 4 }}>
      {/* ── Page Header (Consistent with Audits and Projects pages) ── */}
      <Stack
        component="div"
        direction={{ xs: 'column', sm: 'row' }}
        sx={{
          justifyContent: 'space-between',
          alignItems: { xs: 'flex-start', sm: 'center' },
          mb: 4,
          gap: 2,
        }}
      >
        <Box>
          <Typography
            variant="h4"
            sx={{ fontWeight: 800, mb: 0.5, letterSpacing: '-0.5px' }}
          >
            Estimation
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Evaluate page complexity across Simple, Medium, and Complex tiers to generate commercial audit proposals.
          </Typography>
        </Box>

        {/* Action Buttons (Visible when results are ready) */}
        {result && (
          <Stack component="div" direction="row" spacing={1.5} sx={{ flexWrap: 'wrap' }}>
            <Button
              variant="contained"
              color="success"
              startIcon={
                exportingExcel ? <CircularProgress size={16} color="inherit" /> : <FileDownloadIcon />
              }
              onClick={handleDownloadExcel}
              disabled={exportingExcel}
              sx={{ fontWeight: 700, textTransform: 'none', borderRadius: 2 }}
            >
              {exportingExcel ? 'Exporting...' : 'Excel Quote'}
            </Button>
            <Button
              variant="contained"
              color="primary"
              startIcon={
                exportingPdf ? <CircularProgress size={16} color="inherit" /> : <DescriptionIcon />
              }
              onClick={handleDownloadPdf}
              disabled={exportingPdf}
              sx={{ fontWeight: 700, textTransform: 'none', borderRadius: 2 }}
            >
              {exportingPdf ? 'Exporting...' : 'PDF Proposal'}
            </Button>
            <Button
              variant="outlined"
              startIcon={<PrintIcon />}
              onClick={() => window.print()}
              sx={{ fontWeight: 700, textTransform: 'none', borderRadius: 2 }}
            >
              Print
            </Button>
          </Stack>
        )}
      </Stack>

      {/* ── Mode Selection & URL Input Card ── */}
      <EstimationUrlInputCard
        inputMode={inputMode}
        onInputModeChange={setInputMode}
        baseUrl={baseUrl}
        onBaseUrlChange={setBaseUrl}
        discoveryDepth={discoveryDepth}
        onDiscoveryDepthChange={setDiscoveryDepth}
        maxDiscovery={maxDiscovery}
        onMaxDiscoveryChange={setMaxDiscovery}
        discovering={discovering}
        onDiscover={handleDiscover}
        discoveredPages={discoveredPages}
        selectedUrls={selectedUrls}
        onToggleUrl={handleToggleUrl}
        onSelectAll={handleSelectAll}
        onDeselectAll={handleDeselectAll}
        filterKeyword={filterKeyword}
        onFilterKeywordChange={setFilterKeyword}
        customUrlsText={customUrlsText}
        onCustomUrlsTextChange={setCustomUrlsText}
        analyzing={analyzing}
        onAnalyzeSelected={handleAnalyzeSelected}
      />

      {/* Error Banner */}
      {error && (
        <Alert severity="error" sx={{ mb: 4, borderRadius: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* Analyzing Progress State */}
      {analyzing && (
        <Card
          sx={{
            mb: 4,
            p: 4,
            borderRadius: 3,
            textAlign: 'center',
            bgcolor: alpha(theme.palette.background.default, 0.8),
            border: '1px solid',
            borderColor: theme.palette.divider,
          }}
        >
          <CircularProgress size={42} sx={{ mb: 2, color: theme.palette.primary.main }} />
          <Typography variant="h6" sx={{ fontWeight: 800, mb: 0.5, color: theme.palette.text.primary }}>
            Evaluating Page Complexity & Element Inventories...
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Launching headless browser sandbox, inspecting DOM nodes, and matching WCAG criteria complexity profiles.
          </Typography>
        </Card>
      )}

      {/* ── Complexity Standards Collapsible Guide ── */}
      <ComplexityMatrixGuide
        expanded={showCriteriaGuide}
        onToggle={() => setShowCriteriaGuide((prev) => !prev)}
      />

      {/* ── Results Section ── */}
      {result && (
        <>
          {/* Rate & Commercial Configurator Card */}
          <CommercialRateConfigurator
            hourlyRate={hourlyRate}
            platformFee={platformFee}
            profitMarginPct={profitMarginPct}
            onRateChange={handleRateConfigurationChange}
          />

          {/* KPI Dashboard Cards */}
          <EstimationKpiCards summary={result.summary} />

          {/* Complexity Breakdown Strip & Multi-Segment Progress Bar */}
          <ComplexityDistributionCard summary={result.summary} />

          {/* Page-by-Page Detailed Table */}
          <EstimationLineItemsTable
            result={result}
            expandedRows={expandedRows}
            onToggleRow={toggleRow}
            onComplexityOverride={handlePageComplexityOverride}
            exportingExcel={exportingExcel}
            exportingPdf={exportingPdf}
            onDownloadExcel={handleDownloadExcel}
            onDownloadPdf={handleDownloadPdf}
          />
        </>
      )}
    </Box>
  );
};

export default EstimationPage;
