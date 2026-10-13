import React, { useEffect, useState } from 'react';
import {
  Box,
  Typography,
  Stack,
  Button,
  CircularProgress,
  Alert,
  Chip,
  useTheme,
} from '@mui/material';
import { alpha } from '@mui/material/styles';
import { useParams, useNavigate } from '@tanstack/react-router';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import FileDownloadIcon from '@mui/icons-material/FileDownload';
import DescriptionIcon from '@mui/icons-material/Description';
import PrintIcon from '@mui/icons-material/Print';
import LanguageIcon from '@mui/icons-material/Language';
import InfoOutlinedIcon from '@mui/icons-material/InfoOutlined';
import Tooltip from '@mui/material/Tooltip';

import { estimationService } from '../../service/estimationService';
import type {
  SavedEstimateRecord,
  EstimatedPage,
  EstimationSummary,
} from '../../service/estimationService';

import {
  CommercialRateConfigurator,
  EstimationKpiCards,
  ComplexityDistributionCard,
  EstimationLineItemsTable,
  ComplexityMatrixGuide,
} from '../../components/estimation';

export const EstimationDetailsPage: React.FC = () => {
  const theme = useTheme();
  const navigate = useNavigate();
  const { orgId, estimateId } = useParams({ strict: false }) as any;

  const [loading, setLoading] = useState(true);
  const [estimate, setEstimate] = useState<
    (SavedEstimateRecord & { pages: EstimatedPage[]; summary: EstimationSummary }) | null
  >(null);
  const [error, setError] = useState<string | null>(null);

  // Expanded rows state for line items table
  const [expandedRows, setExpandedRows] = useState<Record<number, boolean>>({});
  const [showCriteriaGuide, setShowCriteriaGuide] = useState(false);

  // Export progress
  const [exportingExcel, setExportingExcel] = useState(false);
  const [exportingPdf, setExportingPdf] = useState(false);

  const fetchEstimate = async () => {
    if (!estimateId) return;
    setLoading(true);
    setError(null);
    try {
      const data = await estimationService.get(estimateId);
      setEstimate(data);
    } catch (err: any) {
      console.error('Failed to load estimation:', err);
      setError(err?.response?.data?.detail || err?.message || 'Failed to load estimation details.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchEstimate();
  }, [estimateId]);

  const toggleRow = (idx: number) => {
    setExpandedRows((prev) => ({
      ...prev,
      [idx]: !prev[idx],
    }));
  };

  // Recalculate & save modified rates or manual tier overrides
  const handleRateConfigurationChange = async (
    newHourlyRate: number,
    newPlatformFee: number,
    newProfitMarginPct: number
  ) => {
    if (!estimate) return;
    try {
      const updated = await estimationService.update(estimate.id, {
        hourly_rate: newHourlyRate,
        platform_fee: newPlatformFee,
        profit_margin_pct: newProfitMarginPct,
        pages: estimate.pages,
      });
      setEstimate(updated);
    } catch (err: any) {
      console.error('Failed to update rates:', err);
      setError('Failed to update commercial rates.');
    }
  };

  const handlePageComplexityOverride = async (
    pageIndex: number,
    newComplexity: 'simple' | 'medium' | 'complex'
  ) => {
    if (!estimate) return;
    const updatedPages = [...estimate.pages];
    const targetPage = { ...updatedPages[pageIndex] };
    targetPage.complexity = newComplexity;
    targetPage.complexity_label =
      newComplexity === 'simple' ? 'Simple' : newComplexity === 'medium' ? 'Medium' : 'Complex';
    targetPage.summary_rationale = `Manual auditor override applied: Set to ${targetPage.complexity_label}.`;
    targetPage.triggers = [`Auditor override: ${targetPage.complexity_label} tier`];
    updatedPages[pageIndex] = targetPage;

    try {
      const updated = await estimationService.update(estimate.id, {
        pages: updatedPages,
      });
      setEstimate(updated);
    } catch (err: any) {
      console.error('Failed to save tier override:', err);
      setError('Failed to save manual complexity override.');
    }
  };

  // Export handlers
  const handleDownloadExcel = async () => {
    if (!estimate) return;
    setExportingExcel(true);
    try {
      await estimationService.downloadQuotationExcel({
        summary: estimate.summary,
        pages: estimate.pages,
      });
    } catch (err: any) {
      console.error('Failed to export Excel quote:', err);
      setError('Failed to download Excel proposal.');
    } finally {
      setExportingExcel(false);
    }
  };

  const handleDownloadPdf = async () => {
    if (!estimate) return;
    setExportingPdf(true);
    try {
      await estimationService.downloadQuotationPdf({
        summary: estimate.summary,
        pages: estimate.pages,
      });
    } catch (err: any) {
      console.error('Failed to export PDF proposal:', err);
      setError('Failed to download PDF proposal.');
    } finally {
      setExportingPdf(false);
    }
  };

  if (loading) {
    return (
      <Box sx={{ p: 6, textAlign: 'center' }}>
        <CircularProgress size={42} sx={{ mb: 2 }} />
        <Typography variant="body1" color="text.secondary">
          Loading estimation details...
        </Typography>
      </Box>
    );
  }

  if (error || !estimate) {
    return (
      <Box sx={{ p: 3 }}>
        <Button
          startIcon={<ArrowBackIcon />}
          onClick={() => navigate({ to: `/org/${orgId}/estimation` })}
          sx={{ mb: 2, fontWeight: 700 }}
        >
          Back to Estimations
        </Button>
        <Alert severity="error" sx={{ borderRadius: 2 }}>
          {error || 'Estimation not found.'}
        </Alert>
      </Box>
    );
  }

  const resultPayload = {
    pages: estimate.pages,
    summary: estimate.summary,
  };

  return (
    <Box sx={{ pb: 6 }}>
      {/* ── Breadcrumb & Top Action Header ── */}
      <Stack
        component="div"
        direction={{ xs: 'column', md: 'row' }}
        sx={{
          justifyContent: 'space-between',
          alignItems: { xs: 'flex-start', md: 'center' },
          mb: 3,
          gap: 2,
        }}
      >
        <Box>
          <Button
            startIcon={<ArrowBackIcon />}
            onClick={() => navigate({ to: `/org/${orgId}/estimation` })}
            size="small"
            sx={{
              fontWeight: 700,
              textTransform: 'none',
              color: 'text.secondary',
              mb: 1,
              px: 0,
              '&:hover': { bgcolor: 'transparent', color: 'primary.main' },
            }}
          >
            Back to Estimations
          </Button>

          <Typography variant="h4" sx={{ fontWeight: 800, letterSpacing: '-0.5px', mb: 0.75 }}>
            {estimate.title}
          </Typography>

          <Stack component="div" direction="row" spacing={1.5} sx={{ alignItems: 'center', flexWrap: 'wrap' }}>
            <Chip
              icon={<LanguageIcon />}
              label={estimate.base_url}
              size="small"
              variant="outlined"
              sx={{ fontWeight: 600 }}
            />
            <Chip
              label={estimate.mode === 'discover' ? 'Crawl Discovery' : 'Direct URL List'}
              size="small"
              sx={{ fontWeight: 600, bgcolor: alpha(theme.palette.info.main, 0.08), color: theme.palette.info.dark }}
            />
            <Typography variant="caption" color="text.secondary">
              Created on{' '}
              {new Date(estimate.created_at).toLocaleDateString(undefined, {
                year: 'numeric',
                month: 'short',
                day: 'numeric',
              })}
            </Typography>
          </Stack>
        </Box>

        {/* Action Buttons */}
        <Stack component="div" direction="row" spacing={1.5} sx={{ flexWrap: 'wrap', flexShrink: 0 }}>
          <Tooltip title="View Complexity Classification Matrix">
            <Button
              variant="outlined"
              color="inherit"
              size="small"
              startIcon={<InfoOutlinedIcon color="primary" />}
              onClick={() => setShowCriteriaGuide(true)}
              sx={{
                fontWeight: 700,
                textTransform: 'none',
                borderRadius: 2,
                borderColor: theme.palette.divider,
                bgcolor: theme.palette.background.paper,
                color: theme.palette.text.primary,
              }}
            >
              Complexity Guide
            </Button>
          </Tooltip>

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
      </Stack>

      {/* ── Commercial Rates Configurator (Live adjuster) ── */}
      <CommercialRateConfigurator
        hourlyRate={estimate.hourly_rate}
        platformFee={estimate.platform_fee}
        profitMarginPct={estimate.profit_margin_pct}
        onRateChange={handleRateConfigurationChange}
      />

      {/* ── KPI Dashboard Cards ── */}
      <EstimationKpiCards summary={estimate.summary} />

      {/* ── Complexity Breakdown Distribution Strip ── */}
      <ComplexityDistributionCard summary={estimate.summary} />

      {/* ── Page-by-Page Detailed Line Items Table ── */}
      <EstimationLineItemsTable
        result={resultPayload}
        expandedRows={expandedRows}
        onToggleRow={toggleRow}
        onComplexityOverride={handlePageComplexityOverride}
        exportingExcel={exportingExcel}
        exportingPdf={exportingPdf}
        onDownloadExcel={handleDownloadExcel}
        onDownloadPdf={handleDownloadPdf}
      />

      {/* Complexity Guide Modal */}
      <ComplexityMatrixGuide
        open={showCriteriaGuide}
        onClose={() => setShowCriteriaGuide(false)}
      />
    </Box>
  );
};

export default EstimationDetailsPage;
