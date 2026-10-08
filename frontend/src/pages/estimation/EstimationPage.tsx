import React, { useState } from 'react';
import {
  Box,
  Typography,
  Stack,
  Card,
  CardContent,
  TextField,
  Button,
  Grid,
  Chip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableFooter,
  TableRow,
  Paper,
  CircularProgress,
  Alert,
  InputAdornment,
  Divider,
  Collapse,
  IconButton,
  Tabs,
  Tab,
  Checkbox,
  Tooltip,
  Select,
  MenuItem
} from '@mui/material';
import CalculateIcon from '@mui/icons-material/Calculate';
import LanguageIcon from '@mui/icons-material/Language';
import AccessTimeIcon from '@mui/icons-material/AccessTime';
import MonetizationOnIcon from '@mui/icons-material/MonetizationOn';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import LayersIcon from '@mui/icons-material/Layers';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import ExpandLessIcon from '@mui/icons-material/ExpandLess';
import PrintIcon from '@mui/icons-material/Print';
import InfoOutlinedIcon from '@mui/icons-material/InfoOutlined';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import FileDownloadIcon from '@mui/icons-material/FileDownload';
import DescriptionIcon from '@mui/icons-material/Description';
import TravelExploreIcon from '@mui/icons-material/TravelExplore';
import LinkIcon from '@mui/icons-material/Link';
import SearchIcon from '@mui/icons-material/Search';
import PlaylistAddCheckIcon from '@mui/icons-material/PlaylistAddCheck';
import BoltIcon from '@mui/icons-material/Bolt';
import WarningAmberIcon from '@mui/icons-material/WarningAmber';
import ArrowForwardIcon from '@mui/icons-material/ArrowForward';
import RefreshIcon from '@mui/icons-material/Refresh';
import OpenInNewIcon from '@mui/icons-material/OpenInNew';
import TuneIcon from '@mui/icons-material/Tune';

import { estimationService } from '../../service/estimationService';
import type {
  EstimationResult,
  EstimatedPage,
  DiscoveredUrlItem
} from '../../service/estimationService';

export const EstimationPage: React.FC = () => {
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

  const selectedCount = Object.values(selectedUrls).filter(Boolean).length;
  const parsedCustomUrls = getParsedCustomUrls();

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
      targetUrls = parsedCustomUrls;
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

  const getComplexityColor = (c: string): 'success' | 'warning' | 'error' | 'default' => {
    switch (c?.toLowerCase()) {
      case 'simple':
        return 'success';
      case 'medium':
        return 'warning';
      case 'complex':
        return 'error';
      default:
        return 'default';
    }
  };

  const filteredDiscoveredPages = discoveredPages.filter((item) => {
    if (!filterKeyword) return true;
    const k = filterKeyword.toLowerCase();
    return item.path.toLowerCase().includes(k) || item.url.toLowerCase().includes(k);
  });

  // Calculate percentage ratios for the complexity distribution bar
  const totalPages = result?.summary.total_pages || 0;
  const simplePct = totalPages > 0 ? ((result?.summary.simple_pages || 0) / totalPages) * 100 : 0;
  const mediumPct = totalPages > 0 ? ((result?.summary.medium_pages || 0) / totalPages) * 100 : 0;
  const complexPct = totalPages > 0 ? ((result?.summary.complex_pages || 0) / totalPages) * 100 : 0;

  return (
    <Box sx={{ maxWidth: 1440, mx: 'auto', p: { xs: 2, sm: 3, md: 4 } }}>
      {/* ── Executive Hero Header ────────────────────────────────────────── */}
      <Box
        sx={{
          mb: 4,
          p: { xs: 3, md: 4 },
          borderRadius: '20px',
          background: 'linear-gradient(135deg, #090D16 0%, #0F172A 40%, #1E1B4B 100%)',
          color: '#FFFFFF',
          position: 'relative',
          overflow: 'hidden',
          boxShadow: '0 12px 36px -4px rgba(15, 23, 42, 0.45)',
          border: '1px solid rgba(255, 255, 255, 0.08)',
        }}
      >
        <Stack
          component="div"
          direction={{ xs: 'column', md: 'row' }}
          spacing={3}
          sx={{ justifyContent: 'space-between', alignItems: { xs: 'flex-start', md: 'center' } }}
        >
          <Box sx={{ maxWidth: 760 }}>
            <Stack component="div" direction="row" spacing={1.5} sx={{ alignItems: 'center', mb: 1.5 }}>
              <Chip
                icon={<TuneIcon sx={{ fontSize: 16, color: '#38BDF8 !important' }} />}
                label="Commercial Scoping & Valuation Engine"
                size="small"
                sx={{
                  bgcolor: 'rgba(56, 189, 248, 0.12)',
                  color: '#38BDF8',
                  fontWeight: '700',
                  fontSize: '0.75rem',
                  border: '1px solid rgba(56, 189, 248, 0.3)',
                }}
              />
              <Chip
                label="WCAG 2.1 / 2.2 Auditing Standards"
                size="small"
                sx={{
                  bgcolor: 'rgba(255, 255, 255, 0.08)',
                  color: '#94A3B8',
                  fontWeight: '600',
                  fontSize: '0.75rem',
                }}
              />
            </Stack>
            <Typography
              variant="h3"
              sx={{
                fontWeight: '800',
                letterSpacing: '-0.025em',
                color: '#FFFFFF',
                mb: 1,
                fontSize: { xs: '1.75rem', md: '2.35rem' },
              }}
            >
              Accessibility Audit Estimation & Proposal Engine
            </Typography>
            <Typography
              variant="body1"
              sx={{ color: '#94A3B8', lineHeight: 1.6, fontSize: { xs: '0.9rem', md: '1.025rem' } }}
            >
              Evaluate DOM complexity across Simple (1.0h), Medium (2.5h), and Complex (5.5h) tiers.
              Calculates manual verification hours, cloud scanning fees, and a 30% agency margin to
              produce client-ready commercial proposals.
            </Typography>
          </Box>

          {/* Quick Export Actions (When result is available) */}
          {result && (
            <Stack
              component="div"
              direction={{ xs: 'column', sm: 'row' }}
              spacing={1.5}
              sx={{ width: { xs: '100%', md: 'auto' } }}
            >
              <Button
                variant="contained"
                startIcon={
                  exportingExcel ? <CircularProgress size={16} color="inherit" /> : <FileDownloadIcon />
                }
                onClick={handleDownloadExcel}
                disabled={exportingExcel}
                sx={{
                  bgcolor: '#10B981',
                  color: '#FFFFFF',
                  fontWeight: '700',
                  borderRadius: '10px',
                  textTransform: 'none',
                  px: 2.5,
                  py: 1.2,
                  boxShadow: '0 4px 14px rgba(16, 185, 129, 0.35)',
                  '&:hover': { bgcolor: '#059669', transform: 'translateY(-1px)' },
                  transition: 'all 0.2s cubic-bezier(0.16, 1, 0.3, 1)',
                }}
              >
                {exportingExcel ? 'Exporting...' : 'Excel Quote (.xlsx)'}
              </Button>
              <Button
                variant="contained"
                startIcon={
                  exportingPdf ? <CircularProgress size={16} color="inherit" /> : <DescriptionIcon />
                }
                onClick={handleDownloadPdf}
                disabled={exportingPdf}
                sx={{
                  bgcolor: '#3B82F6',
                  color: '#FFFFFF',
                  fontWeight: '700',
                  borderRadius: '10px',
                  textTransform: 'none',
                  px: 2.5,
                  py: 1.2,
                  boxShadow: '0 4px 14px rgba(59, 130, 246, 0.35)',
                  '&:hover': { bgcolor: '#2563EB', transform: 'translateY(-1px)' },
                  transition: 'all 0.2s cubic-bezier(0.16, 1, 0.3, 1)',
                }}
              >
                {exportingPdf ? 'Exporting...' : 'PDF Proposal (.pdf)'}
              </Button>
              <Button
                variant="outlined"
                startIcon={<PrintIcon />}
                onClick={() => window.print()}
                sx={{
                  borderColor: 'rgba(255, 255, 255, 0.2)',
                  color: '#E2E8F0',
                  fontWeight: '700',
                  borderRadius: '10px',
                  textTransform: 'none',
                  '&:hover': { borderColor: '#FFFFFF', bgcolor: 'rgba(255, 255, 255, 0.05)' },
                }}
              >
                Print
              </Button>
            </Stack>
          )}
        </Stack>
      </Box>

      {/* ── Mode Selection & URL Input Card ──────────────────────────────── */}
      <Card
        sx={{
          mb: 4,
          borderRadius: '16px',
          border: '1px solid',
          borderColor: 'divider',
          boxShadow: '0 4px 20px -2px rgba(15, 23, 42, 0.05)',
          overflow: 'hidden',
        }}
      >
        <Box sx={{ borderBottom: 1, borderColor: 'divider', bgcolor: 'rgba(248, 250, 252, 0.8)', px: 2, pt: 1 }}>
          <Tabs
            value={inputMode}
            onChange={(_, val) => setInputMode(val)}
            textColor="primary"
            indicatorColor="primary"
            sx={{
              '& .MuiTabs-indicator': { height: 3, borderRadius: '3px 3px 0 0' },
            }}
          >
            <Tab
              icon={<TravelExploreIcon sx={{ fontSize: 19 }} />}
              iconPosition="start"
              label="Mode A: Discover from Base URL (Crawl & Select)"
              sx={{ fontWeight: '700', textTransform: 'none', py: 1.8, fontSize: '0.925rem' }}
            />
            <Tab
              icon={<LinkIcon sx={{ fontSize: 19 }} />}
              iconPosition="start"
              label="Mode B: Direct URL List (Client-Provided URLs)"
              sx={{ fontWeight: '700', textTransform: 'none', py: 1.8, fontSize: '0.925rem' }}
            />
          </Tabs>
        </Box>

        <CardContent sx={{ p: { xs: 2.5, md: 3.5 } }}>
          {/* Quick Preset Buttons */}
          <Stack
            component="div"
            direction="row"
            spacing={1}
            sx={{ alignItems: 'center', mb: 2.5, flexWrap: 'wrap', gap: 1 }}
          >
            <Typography variant="caption" sx={{ fontWeight: '700', color: 'text.secondary', mr: 0.5 }}>
              QUICK SAMPLE PRESETS:
            </Typography>
            <Chip
              label="WinVinaya.com (Corporate Static)"
              size="small"
              clickable
              onClick={() => {
                if (inputMode === 0) {
                  setBaseUrl('https://winvinaya.com');
                } else {
                  setCustomUrlsText(
                    'https://winvinaya.com\nhttps://winvinaya.com/about-us/\nhttps://winvinaya.com/contact-us/'
                  );
                }
              }}
              sx={{
                fontWeight: '600',
                bgcolor: 'rgba(59, 130, 246, 0.08)',
                color: '#2563EB',
                border: '1px solid rgba(59, 130, 246, 0.2)',
                '&:hover': { bgcolor: 'rgba(59, 130, 246, 0.16)' },
              }}
            />
            <Chip
              label="Lemonn.co.in (FinTech Portal)"
              size="small"
              clickable
              onClick={() => {
                if (inputMode === 0) {
                  setBaseUrl('https://lemonn.co.in');
                } else {
                  setCustomUrlsText(
                    'https://lemonn.co.in/\nhttps://lemonn.co.in/ipo\nhttps://lemonn.co.in/mutual-funds'
                  );
                }
              }}
              sx={{
                fontWeight: '600',
                bgcolor: 'rgba(16, 185, 129, 0.08)',
                color: '#059669',
                border: '1px solid rgba(16, 185, 129, 0.2)',
                '&:hover': { bgcolor: 'rgba(16, 185, 129, 0.16)' },
              }}
            />
          </Stack>

          {/* Mode 0: Crawl & Discover from Base URL */}
          {inputMode === 0 && (
            <Box>
              <form onSubmit={handleDiscover}>
                <Grid container spacing={2.5} component="div" sx={{ alignItems: 'flex-start' }}>
                  <Grid size={{ xs: 12, md: 6 }} component="div">
                    <Typography variant="caption" sx={{ fontWeight: '700', color: 'text.secondary', display: 'block', mb: 0.75 }}>
                      TARGET ROOT DOMAIN / BASE URL
                    </Typography>
                    <TextField
                      fullWidth
                      placeholder="https://winvinaya.com"
                      value={baseUrl}
                      onChange={(e) => setBaseUrl(e.target.value)}
                      required
                      slotProps={{
                        input: {
                          startAdornment: (
                            <InputAdornment position="start">
                              <LanguageIcon color="action" />
                            </InputAdornment>
                          ),
                        },
                      }}
                      helperText="System will extract internal routes and present an interactive selection matrix."
                    />
                  </Grid>

                  <Grid size={{ xs: 6, md: 2 }} component="div">
                    <Typography variant="caption" sx={{ fontWeight: '700', color: 'text.secondary', display: 'block', mb: 0.75 }}>
                      CRAWL DEPTH
                    </Typography>
                    <TextField
                      fullWidth
                      select
                      value={discoveryDepth}
                      onChange={(e) => setDiscoveryDepth(Number(e.target.value))}
                      slotProps={{ select: { native: true } }}
                    >
                      <option value={1}>Level 1 (Direct Links)</option>
                      <option value={2}>Level 2 (Internal Sub-pages)</option>
                      <option value={3}>Level 3 (Deep Discovery)</option>
                    </TextField>
                  </Grid>

                  <Grid size={{ xs: 6, md: 2 }} component="div">
                    <Typography variant="caption" sx={{ fontWeight: '700', color: 'text.secondary', display: 'block', mb: 0.75 }}>
                      MAX DISCOVERY
                    </Typography>
                    <TextField
                      fullWidth
                      type="number"
                      value={maxDiscovery}
                      onChange={(e) => setMaxDiscovery(Math.max(5, Number(e.target.value)))}
                      slotProps={{ htmlInput: { min: 5, max: 100 } }}
                    />
                  </Grid>

                  <Grid size={{ xs: 12, md: 2 }} component="div">
                    <Typography variant="caption" sx={{ visibility: 'hidden', display: 'block', mb: 0.75 }}>
                      ACTION
                    </Typography>
                    <Button
                      type="submit"
                      variant="contained"
                      color="primary"
                      fullWidth
                      size="large"
                      disabled={discovering || !baseUrl.trim()}
                      startIcon={discovering ? <CircularProgress size={18} color="inherit" /> : <TravelExploreIcon />}
                      sx={{
                        py: 1.6,
                        fontWeight: '700',
                        borderRadius: '10px',
                        textTransform: 'none',
                        boxShadow: '0 4px 14px rgba(26, 35, 126, 0.25)',
                      }}
                    >
                      {discovering ? 'Discovering...' : 'Discover Pages'}
                    </Button>
                  </Grid>
                </Grid>
              </form>

              {/* Discovered URLs List / Selector */}
              {discoveredPages.length > 0 && (
                <Box
                  sx={{
                    mt: 3.5,
                    p: 3,
                    bgcolor: 'rgba(248, 250, 252, 0.85)',
                    borderRadius: '14px',
                    border: '1px solid',
                    borderColor: 'divider',
                  }}
                >
                  <Stack
                    component="div"
                    direction={{ xs: 'column', sm: 'row' }}
                    spacing={2}
                    sx={{ justifyContent: 'space-between', alignItems: { xs: 'flex-start', sm: 'center' }, mb: 2 }}
                  >
                    <Box>
                      <Stack component="div" direction="row" spacing={1} sx={{ alignItems: 'center', mb: 0.5 }}>
                        <PlaylistAddCheckIcon color="primary" />
                        <Typography variant="subtitle1" sx={{ fontWeight: '800' }}>
                          Discovered Pages ({discoveredPages.length})
                        </Typography>
                        <Chip
                          label={`${selectedCount} Selected`}
                          size="small"
                          color={selectedCount > 0 ? 'primary' : 'default'}
                          sx={{ fontWeight: '800' }}
                        />
                      </Stack>
                      <Typography variant="caption" color="text.secondary">
                        Select the exact URLs you need audited. Unchecked routes will be excluded from the estimation.
                      </Typography>
                    </Box>

                    <Stack component="div" direction="row" spacing={1} sx={{ alignItems: 'center', flexWrap: 'wrap' }}>
                      <TextField
                        size="small"
                        placeholder="Search path/keyword..."
                        value={filterKeyword}
                        onChange={(e) => setFilterKeyword(e.target.value)}
                        slotProps={{
                          input: {
                            startAdornment: (
                              <InputAdornment position="start">
                                <SearchIcon fontSize="small" color="action" />
                              </InputAdornment>
                            ),
                          },
                        }}
                        sx={{ width: { xs: '100%', sm: 220 }, bgcolor: '#FFFFFF' }}
                      />
                      <Button size="small" variant="outlined" onClick={handleSelectAll} sx={{ fontWeight: '700', textTransform: 'none' }}>
                        Select All
                      </Button>
                      <Button size="small" variant="outlined" color="inherit" onClick={handleDeselectAll} sx={{ fontWeight: '700', textTransform: 'none' }}>
                        Deselect All
                      </Button>
                    </Stack>
                  </Stack>

                  {/* Scrollable Checkbox Table */}
                  <TableContainer
                    component={Paper}
                    sx={{
                      maxHeight: 280,
                      border: '1px solid',
                      borderColor: 'divider',
                      borderRadius: '10px',
                      mb: 2.5,
                      boxShadow: 'none',
                    }}
                  >
                    <Table size="small" stickyHeader>
                      <TableHead>
                        <TableRow>
                          <TableCell padding="checkbox" sx={{ bgcolor: '#F1F5F9', width: 48 }}>
                            <Checkbox
                              indeterminate={selectedCount > 0 && selectedCount < discoveredPages.length}
                              checked={discoveredPages.length > 0 && selectedCount === discoveredPages.length}
                              onChange={(e) => (e.target.checked ? handleSelectAll() : handleDeselectAll())}
                            />
                          </TableCell>
                          <TableCell sx={{ bgcolor: '#F1F5F9', fontWeight: '800', width: 220 }}>Route Path</TableCell>
                          <TableCell sx={{ bgcolor: '#F1F5F9', fontWeight: '800' }}>Full Target URL</TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {filteredDiscoveredPages.map((item, idx) => {
                          const isChecked = !!selectedUrls[item.url];
                          return (
                            <TableRow
                              key={idx}
                              hover
                              onClick={() => handleToggleUrl(item.url)}
                              sx={{
                                cursor: 'pointer',
                                bgcolor: isChecked ? 'rgba(59, 130, 246, 0.05)' : undefined,
                                transition: 'background-color 0.15s ease',
                              }}
                            >
                              <TableCell padding="checkbox">
                                <Checkbox checked={isChecked} />
                              </TableCell>
                              <TableCell>
                                <Chip
                                  label={item.path}
                                  size="small"
                                  variant="outlined"
                                  sx={{
                                    fontFamily: 'Consolas, monospace',
                                    fontWeight: '700',
                                    color: isChecked ? 'primary.main' : 'text.secondary',
                                    borderColor: isChecked ? 'primary.main' : 'divider',
                                  }}
                                />
                              </TableCell>
                              <TableCell sx={{ color: 'text.secondary', fontSize: '0.85rem', wordBreak: 'break-all' }}>
                                {item.url}
                              </TableCell>
                            </TableRow>
                          );
                        })}
                      </TableBody>
                    </Table>
                  </TableContainer>

                  {/* Action to Calculate Estimation on Selected */}
                  <Stack
                    component="div"
                    direction={{ xs: 'column', sm: 'row' }}
                    sx={{ justifyContent: 'space-between', alignItems: 'center' }}
                  >
                    <Typography variant="body2" color="text.secondary">
                      {selectedCount === 0
                        ? 'Select at least one route above to proceed.'
                        : `Ready to audit and estimate ${selectedCount} selected page(s).`}
                    </Typography>
                    <Button
                      variant="contained"
                      color="primary"
                      size="large"
                      onClick={handleAnalyzeSelected}
                      disabled={analyzing || selectedCount === 0}
                      startIcon={analyzing ? <CircularProgress size={18} color="inherit" /> : <CalculateIcon />}
                      endIcon={<ArrowForwardIcon />}
                      sx={{
                        fontWeight: '800',
                        px: 4,
                        py: 1.5,
                        borderRadius: '10px',
                        textTransform: 'none',
                        boxShadow: '0 4px 16px rgba(26, 35, 126, 0.3)',
                      }}
                    >
                      {analyzing ? 'Analyzing Page Complexity...' : `Calculate Estimation for (${selectedCount}) Pages`}
                    </Button>
                  </Stack>
                </Box>
              )}
            </Box>
          )}

          {/* Mode 1: Direct Custom URL List */}
          {inputMode === 1 && (
            <Box>
              <Typography variant="caption" sx={{ fontWeight: '700', color: 'text.secondary', display: 'block', mb: 1 }}>
                PASTE CLIENT-SPECIFIED URLS (ONE PER LINE OR COMMA-SEPARATED)
              </Typography>
              <TextField
                fullWidth
                multiline
                rows={6}
                placeholder={`https://winvinaya.com\nhttps://winvinaya.com/about-us/\nhttps://winvinaya.com/contact-us/`}
                value={customUrlsText}
                onChange={(e) => setCustomUrlsText(e.target.value)}
                helperText="Paste arbitrary URLs across the same or different domains. Each line is evaluated as an individual audit line item."
                sx={{
                  mb: 2.5,
                  '& .MuiInputBase-input': {
                    fontFamily: 'Consolas, Monaco, "Courier New", monospace',
                    fontSize: '0.9rem',
                    lineHeight: 1.6,
                  },
                }}
              />

              <Stack
                component="div"
                direction={{ xs: 'column', sm: 'row' }}
                sx={{ justifyContent: 'space-between', alignItems: 'center' }}
              >
                <Chip
                  icon={<PlaylistAddCheckIcon />}
                  label={`${parsedCustomUrls.length} Valid URL(s) Parsed`}
                  color={parsedCustomUrls.length > 0 ? 'primary' : 'default'}
                  sx={{ fontWeight: '700', py: 0.5 }}
                />

                <Button
                  variant="contained"
                  color="primary"
                  size="large"
                  onClick={handleAnalyzeSelected}
                  disabled={analyzing || parsedCustomUrls.length === 0}
                  startIcon={analyzing ? <CircularProgress size={18} color="inherit" /> : <CalculateIcon />}
                  endIcon={<ArrowForwardIcon />}
                  sx={{
                    fontWeight: '800',
                    px: 4,
                    py: 1.5,
                    borderRadius: '10px',
                    textTransform: 'none',
                    boxShadow: '0 4px 16px rgba(26, 35, 126, 0.3)',
                  }}
                >
                  {analyzing ? 'Analyzing Page Complexity...' : `Calculate Estimation for (${parsedCustomUrls.length}) Pages`}
                </Button>
              </Stack>
            </Box>
          )}
        </CardContent>
      </Card>

      {/* Error Banner */}
      {error && (
        <Alert severity="error" sx={{ mb: 4, borderRadius: '10px' }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* Analyzing Progress State */}
      {analyzing && (
        <Card sx={{ mb: 4, p: 4, borderRadius: '16px', textAlign: 'center', bgcolor: 'rgba(248, 250, 252, 0.8)' }}>
          <CircularProgress size={42} sx={{ mb: 2, color: 'primary.main' }} />
          <Typography variant="h6" sx={{ fontWeight: '800', mb: 0.5 }}>
            Evaluating Page Complexity & Element Inventories...
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Launching headless browser sandbox, inspecting DOM nodes, and matching WCAG criteria complexity profiles.
          </Typography>
        </Card>
      )}

      {/* ── Complexity Standards Collapsible Guide ────────────────────────── */}
      <Box sx={{ mb: 4 }}>
        <Button
          variant="text"
          color="inherit"
          onClick={() => setShowCriteriaGuide(!showCriteriaGuide)}
          startIcon={<InfoOutlinedIcon color="primary" />}
          endIcon={showCriteriaGuide ? <ExpandLessIcon /> : <ExpandMoreIcon />}
          sx={{ fontWeight: '700', textTransform: 'none', px: 0, mb: 1 }}
        >
          {showCriteriaGuide ? 'Hide Complexity Classification Matrix' : 'View Complexity Classification Matrix (Simple, Medium, Complex)'}
        </Button>

        <Collapse in={showCriteriaGuide}>
          <Grid container spacing={2.5} component="div" sx={{ mt: 0.5 }}>
            {/* Simple Card */}
            <Grid size={{ xs: 12, md: 4 }} component="div">
              <Card sx={{ bgcolor: 'rgba(16, 185, 129, 0.04)', border: '1px solid rgba(16, 185, 129, 0.25)', borderRadius: '12px' }}>
                <CardContent sx={{ p: 2.5 }}>
                  <Stack component="div" direction="row" spacing={1} sx={{ alignItems: 'center', mb: 1.5 }}>
                    <CheckCircleIcon sx={{ color: '#10B981', fontSize: 20 }} />
                    <Typography variant="subtitle1" sx={{ fontWeight: '800', color: '#065F46' }}>
                      Simple: Static Content (~1.0 Hr)
                    </Typography>
                  </Stack>
                  <Typography variant="body2" sx={{ color: '#047857', lineHeight: 1.6 }}>
                    • Read top-to-bottom with no state mutations<br />
                    • Standard headings, paragraphs, and list hierarchies<br />
                    • Plain links (header, footer, basic navigational bar)<br />
                    • Informative/decorative images and plain buttons<br />
                    • <strong>Total no. of Elements ≤ 50</strong>
                  </Typography>
                </CardContent>
              </Card>
            </Grid>

            {/* Medium Card */}
            <Grid size={{ xs: 12, md: 4 }} component="div">
              <Card sx={{ bgcolor: 'rgba(245, 158, 11, 0.04)', border: '1px solid rgba(245, 158, 11, 0.25)', borderRadius: '12px' }}>
                <CardContent sx={{ p: 2.5 }}>
                  <Stack component="div" direction="row" spacing={1} sx={{ alignItems: 'center', mb: 1.5 }}>
                    <WarningAmberIcon sx={{ color: '#F59E0B', fontSize: 20 }} />
                    <Typography variant="subtitle1" sx={{ fontWeight: '800', color: '#92400E' }}>
                      Medium: Standard Interaction (~2.5 Hrs)
                    </Typography>
                  </Stack>
                  <Typography variant="body2" sx={{ color: '#B45309', lineHeight: 1.6 }}>
                    • Basic forms (inputs, selects, checkboxes, submit)<br />
                    • Data tables with row and column headers<br />
                    • Single embedded video, audio player, or map iframe<br />
                    • Expanding navigation (dropdowns, accordions, tabs)<br />
                    • Search box or <strong>Total no. of Elements &gt; 50 and ≤ 90</strong>
                  </Typography>
                </CardContent>
              </Card>
            </Grid>

            {/* Complex Card */}
            <Grid size={{ xs: 12, md: 4 }} component="div">
              <Card sx={{ bgcolor: 'rgba(239, 68, 68, 0.04)', border: '1px solid rgba(239, 68, 68, 0.25)', borderRadius: '12px' }}>
                <CardContent sx={{ p: 2.5 }}>
                  <Stack component="div" direction="row" spacing={1} sx={{ alignItems: 'center', mb: 1.5 }}>
                    <BoltIcon sx={{ color: '#EF4444', fontSize: 20 }} />
                    <Typography variant="subtitle1" sx={{ fontWeight: '800', color: '#991B1B' }}>
                      Complex: Dynamic Widgets (~5.5 Hrs)
                    </Typography>
                  </Stack>
                  <Typography variant="body2" sx={{ color: '#B91C1C', lineHeight: 1.6 }}>
                    • Pop-up dialogs, cookie banners, focus-shifting modals<br />
                    • Custom widgets (sliders, date pickers, trees, drag-drop)<br />
                    • Multi-step checkout, authentication/OTP/CAPTCHA<br />
                    • Moving content, carousels, live tickers, maps, charts<br />
                    • Complex tables (merged cells, sortable headers)
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </Collapse>
      </Box>

      {/* ── Results Section ───────────────────────────────────────────────── */}
      {result && (
        <>
          {/* Rate & Commercial Configurator Card */}
          <Card
            sx={{
              mb: 4,
              borderRadius: '16px',
              border: '1px solid',
              borderColor: 'divider',
              boxShadow: '0 2px 12px rgba(15, 23, 42, 0.04)',
            }}
          >
            <CardContent sx={{ p: 3 }}>
              <Stack
                component="div"
                direction={{ xs: 'column', sm: 'row' }}
                sx={{ justifyContent: 'space-between', alignItems: { xs: 'flex-start', sm: 'center' }, mb: 2 }}
              >
                <Box>
                  <Typography variant="subtitle2" sx={{ fontWeight: '800', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                    Commercial Rate Configuration (Live Recalculation)
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    Modify hourly auditor rates, platform fees, or margin markups to instantly adjust client proposals.
                  </Typography>
                </Box>
                <Chip icon={<RefreshIcon />} label="Instant Recalculation" size="small" variant="outlined" color="primary" sx={{ fontWeight: '700' }} />
              </Stack>

              <Grid container spacing={3} component="div" sx={{ alignItems: 'center' }}>
                <Grid size={{ xs: 12, sm: 4 }} component="div">
                  <TextField
                    fullWidth
                    size="small"
                    type="number"
                    label="Manual Auditor Hourly Rate ($)"
                    value={hourlyRate}
                    onChange={(e) => {
                      const val = Number(e.target.value);
                      setHourlyRate(val);
                      handleRecalculate(val, platformFee, profitMarginPct);
                    }}
                    slotProps={{
                      input: {
                        startAdornment: <InputAdornment position="start">$</InputAdornment>,
                      },
                    }}
                    helperText="Assistive tech specialist verification fee"
                  />
                </Grid>
                <Grid size={{ xs: 12, sm: 4 }} component="div">
                  <TextField
                    fullWidth
                    size="small"
                    type="number"
                    label="Platform Fee per Page ($)"
                    value={platformFee}
                    onChange={(e) => {
                      const val = Number(e.target.value);
                      setPlatformFee(val);
                      handleRecalculate(hourlyRate, val, profitMarginPct);
                    }}
                    slotProps={{
                      input: {
                        startAdornment: <InputAdornment position="start">$</InputAdornment>,
                      },
                    }}
                    helperText="Cloud orchestration & automated scanning"
                  />
                </Grid>
                <Grid size={{ xs: 12, sm: 4 }} component="div">
                  <TextField
                    fullWidth
                    size="small"
                    type="number"
                    label="Profit Margin Markup (%)"
                    value={profitMarginPct}
                    onChange={(e) => {
                      const val = Number(e.target.value);
                      setProfitMarginPct(val);
                      handleRecalculate(hourlyRate, platformFee, val);
                    }}
                    slotProps={{
                      input: {
                        endAdornment: <InputAdornment position="end">%</InputAdornment>,
                      },
                    }}
                    helperText="Standard commercial agency margin"
                  />
                </Grid>
              </Grid>
            </CardContent>
          </Card>

          {/* KPI Dashboard Cards */}
          <Grid container spacing={3} component="div" sx={{ mb: 4 }}>
            {/* Total Final Quote (Hero Card) */}
            <Grid size={{ xs: 12, sm: 6, md: 3 }} component="div">
              <Card
                sx={{
                  borderRadius: '16px',
                  background: 'linear-gradient(135deg, #0D1B2A 0%, #1A237E 70%, #1565C0 100%)',
                  color: '#FFFFFF',
                  boxShadow: '0 10px 30px -5px rgba(26, 35, 126, 0.4)',
                  border: '1px solid rgba(255, 255, 255, 0.1)',
                  height: '100%',
                }}
              >
                <CardContent sx={{ p: 3 }}>
                  <Stack component="div" direction="row" sx={{ justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                    <Typography variant="overline" sx={{ fontWeight: '800', letterSpacing: '1px', color: '#93C5FD' }}>
                      TOTAL QUOTED INVESTMENT
                    </Typography>
                    <MonetizationOnIcon sx={{ color: '#34D399' }} />
                  </Stack>
                  <Typography variant="h3" sx={{ fontWeight: '800', color: '#34D399', letterSpacing: '-0.02em', mb: 0.5 }}>
                    ${result.summary.total_final_cost.toFixed(2)}
                  </Typography>
                  <Typography variant="caption" sx={{ color: '#E2E8F0', display: 'block' }}>
                    Base Cost + {result.summary.profit_margin_pct}% Agency Margin
                  </Typography>
                </CardContent>
              </Card>
            </Grid>

            {/* Total Manual Hours */}
            <Grid size={{ xs: 12, sm: 6, md: 3 }} component="div">
              <Card
                sx={{
                  borderRadius: '16px',
                  border: '1px solid',
                  borderColor: 'divider',
                  boxShadow: '0 4px 18px rgba(15, 23, 42, 0.04)',
                  height: '100%',
                }}
              >
                <CardContent sx={{ p: 3 }}>
                  <Stack component="div" direction="row" sx={{ justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                    <Typography variant="overline" color="text.secondary" sx={{ fontWeight: '800', letterSpacing: '1px' }}>
                      MANUAL AUDIT EFFORT
                    </Typography>
                    <AccessTimeIcon color="action" />
                  </Stack>
                  <Typography variant="h3" sx={{ fontWeight: '800', color: 'primary.main', mb: 0.5 }}>
                    {result.summary.total_manual_hours.toFixed(1)} <Typography component="span" variant="h5" color="text.secondary">hrs</Typography>
                  </Typography>
                  <Typography variant="caption" color="text.secondary" sx={{ display: 'block' }}>
                    ${result.summary.total_manual_cost.toFixed(2)} @ ${result.summary.hourly_rate}/hr
                  </Typography>
                </CardContent>
              </Card>
            </Grid>

            {/* Base Service Cost */}
            <Grid size={{ xs: 12, sm: 6, md: 3 }} component="div">
              <Card
                sx={{
                  borderRadius: '16px',
                  border: '1px solid',
                  borderColor: 'divider',
                  boxShadow: '0 4px 18px rgba(15, 23, 42, 0.04)',
                  height: '100%',
                }}
              >
                <CardContent sx={{ p: 3 }}>
                  <Stack component="div" direction="row" sx={{ justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                    <Typography variant="overline" color="text.secondary" sx={{ fontWeight: '800', letterSpacing: '1px' }}>
                      BASE SERVICE COST
                    </Typography>
                    <LayersIcon color="action" />
                  </Stack>
                  <Typography variant="h3" sx={{ fontWeight: '800', mb: 0.5 }}>
                    ${result.summary.total_base_cost.toFixed(2)}
                  </Typography>
                  <Typography variant="caption" color="text.secondary" sx={{ display: 'block' }}>
                    API (${result.summary.total_api_cost.toFixed(2)}) + Platform (${result.summary.total_platform_cost.toFixed(2)})
                  </Typography>
                </CardContent>
              </Card>
            </Grid>

            {/* Profit Margin */}
            <Grid size={{ xs: 12, sm: 6, md: 3 }} component="div">
              <Card
                sx={{
                  borderRadius: '16px',
                  border: '1px solid',
                  borderColor: 'divider',
                  boxShadow: '0 4px 18px rgba(15, 23, 42, 0.04)',
                  height: '100%',
                }}
              >
                <CardContent sx={{ p: 3 }}>
                  <Stack component="div" direction="row" sx={{ justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                    <Typography variant="overline" color="text.secondary" sx={{ fontWeight: '800', letterSpacing: '1px' }}>
                      NET PROFIT MARKUP ({result.summary.profit_margin_pct}%)
                    </Typography>
                    <TrendingUpIcon color="success" />
                  </Stack>
                  <Typography variant="h3" sx={{ fontWeight: '800', color: 'success.main', mb: 0.5 }}>
                    ${result.summary.total_profit_margin.toFixed(2)}
                  </Typography>
                  <Typography variant="caption" color="text.secondary" sx={{ display: 'block' }}>
                    Calculated on total base operational costs
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          </Grid>

          {/* Complexity Breakdown Strip & Multi-Segment Progress Bar */}
          <Card sx={{ mb: 4, borderRadius: '16px', border: '1px solid', borderColor: 'divider', overflow: 'hidden' }}>
            <CardContent sx={{ p: 3 }}>
              {/* Distribution Bar */}
              <Box sx={{ mb: 2 }}>
                <Stack component="div" direction="row" sx={{ justifyContent: 'space-between', mb: 1 }}>
                  <Typography variant="caption" sx={{ fontWeight: '800', color: 'text.secondary', textTransform: 'uppercase' }}>
                    Complexity Tier Distribution
                  </Typography>
                  <Typography variant="caption" sx={{ fontWeight: '700', color: 'text.secondary' }}>
                    {result.summary.total_pages} Total Page(s)
                  </Typography>
                </Stack>
                <Box sx={{ display: 'flex', height: 10, borderRadius: 5, overflow: 'hidden', bgcolor: 'rgba(0,0,0,0.06)' }}>
                  {simplePct > 0 && <Box sx={{ width: `${simplePct}%`, bgcolor: '#10B981' }} />}
                  {mediumPct > 0 && <Box sx={{ width: `${mediumPct}%`, bgcolor: '#F59E0B' }} />}
                  {complexPct > 0 && <Box sx={{ width: `${complexPct}%`, bgcolor: '#EF4444' }} />}
                </Box>
              </Box>

              <Divider sx={{ my: 2 }} />

              <Stack component="div" direction={{ xs: 'column', sm: 'row' }} spacing={3} sx={{ alignItems: 'center', justifyContent: 'space-around' }}>
                <Box sx={{ textAlign: 'center' }}>
                  <Typography variant="caption" color="text.secondary" sx={{ fontWeight: '700' }}>
                    TOTAL PAGES AUDITED
                  </Typography>
                  <Typography variant="h5" sx={{ fontWeight: '800' }}>
                    {result.summary.total_pages}
                  </Typography>
                </Box>
                <Divider orientation="vertical" flexItem />
                <Box sx={{ textAlign: 'center' }}>
                  <Typography variant="caption" sx={{ color: '#059669', fontWeight: '700' }}>
                    SIMPLE PAGES (1.0H)
                  </Typography>
                  <Typography variant="h5" sx={{ fontWeight: '800', color: '#059669' }}>
                    {result.summary.simple_pages}
                  </Typography>
                </Box>
                <Divider orientation="vertical" flexItem />
                <Box sx={{ textAlign: 'center' }}>
                  <Typography variant="caption" sx={{ color: '#D97706', fontWeight: '700' }}>
                    MEDIUM PAGES (2.5H)
                  </Typography>
                  <Typography variant="h5" sx={{ fontWeight: '800', color: '#D97706' }}>
                    {result.summary.medium_pages}
                  </Typography>
                </Box>
                <Divider orientation="vertical" flexItem />
                <Box sx={{ textAlign: 'center' }}>
                  <Typography variant="caption" sx={{ color: '#DC2626', fontWeight: '700' }}>
                    COMPLEX PAGES (5.5H)
                  </Typography>
                  <Typography variant="h5" sx={{ fontWeight: '800', color: '#DC2626' }}>
                    {result.summary.complex_pages}
                  </Typography>
                </Box>
              </Stack>
            </CardContent>
          </Card>

          {/* ── Page-by-Page Detailed Table ───────────────────────────────── */}
          <Card
            sx={{
              borderRadius: '16px',
              border: '1px solid',
              borderColor: 'divider',
              boxShadow: '0 4px 20px -2px rgba(15, 23, 42, 0.05)',
              overflow: 'hidden',
            }}
          >
            {/* Table Header Action Bar */}
            <Box sx={{ p: 3, borderBottom: '1px solid', borderColor: 'divider', bgcolor: 'rgba(248, 250, 252, 0.6)' }}>
              <Stack
                component="div"
                direction={{ xs: 'column', sm: 'row' }}
                spacing={2}
                sx={{ justifyContent: 'space-between', alignItems: { xs: 'flex-start', sm: 'center' } }}
              >
                <Box>
                  <Typography variant="h6" sx={{ fontWeight: '800' }}>
                    Page-by-Page Line Items & Cost Breakdown
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    Individual page metrics, automated DOM node counts, manual verification efforts, and final quotes.
                    You can adjust complexity tiers per page to test scenarios.
                  </Typography>
                </Box>
                <Stack component="div" direction="row" spacing={1.5}>
                  <Button
                    size="small"
                    variant="contained"
                    startIcon={exportingExcel ? <CircularProgress size={14} color="inherit" /> : <FileDownloadIcon />}
                    onClick={handleDownloadExcel}
                    disabled={exportingExcel}
                    sx={{
                      bgcolor: '#10B981',
                      color: '#FFFFFF',
                      fontWeight: '700',
                      borderRadius: '8px',
                      textTransform: 'none',
                      '&:hover': { bgcolor: '#059669' },
                    }}
                  >
                    Export Excel
                  </Button>
                  <Button
                    size="small"
                    variant="contained"
                    startIcon={exportingPdf ? <CircularProgress size={14} color="inherit" /> : <DescriptionIcon />}
                    onClick={handleDownloadPdf}
                    disabled={exportingPdf}
                    sx={{
                      bgcolor: '#3B82F6',
                      color: '#FFFFFF',
                      fontWeight: '700',
                      borderRadius: '8px',
                      textTransform: 'none',
                      '&:hover': { bgcolor: '#2563EB' },
                    }}
                  >
                    Export PDF
                  </Button>
                </Stack>
              </Stack>
            </Box>

            <TableContainer>
              <Table>
                <TableHead sx={{ bgcolor: '#F8FAFC' }}>
                  <TableRow>
                    <TableCell sx={{ fontWeight: '800', width: 48 }}>#</TableCell>
                    <TableCell sx={{ fontWeight: '800' }}>Page Title & Target URL</TableCell>
                    <TableCell sx={{ fontWeight: '800' }}>Complexity Tier</TableCell>
                    <TableCell align="center" sx={{ fontWeight: '800' }}>Manual Effort</TableCell>
                    <TableCell align="center" sx={{ fontWeight: '800' }}>Manual Cost</TableCell>
                    <TableCell align="center" sx={{ fontWeight: '800' }}>API Cost</TableCell>
                    <TableCell align="center" sx={{ fontWeight: '800' }}>Platform Fee</TableCell>
                    <TableCell align="right" sx={{ fontWeight: '800' }}>Base Cost (A)</TableCell>
                    <TableCell align="right" sx={{ fontWeight: '800' }}>Margin  ({result.summary.profit_margin_pct}%) (B)</TableCell>
                    <TableCell align="right" sx={{ fontWeight: '800', color: 'primary.main' }}>Total Cost (A+B)</TableCell>
                    <TableCell align="center" sx={{ fontWeight: '800' }}>Evidence</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {result.pages.map((p: EstimatedPage, idx: number) => {
                    const isExpanded = !!expandedRows[idx];
                    return (
                      <React.Fragment key={idx}>
                        <TableRow
                          hover
                          sx={{
                            transition: 'background-color 0.15s ease',
                            bgcolor: isExpanded ? 'rgba(248, 250, 252, 0.8)' : undefined,
                          }}
                        >
                          <TableCell sx={{ fontWeight: '700', color: 'text.secondary' }}>{idx + 1}</TableCell>
                          <TableCell sx={{ maxWidth: '320px' }}>
                            <Typography variant="subtitle2" noWrap sx={{ fontWeight: '700' }}>
                              {p.title}
                            </Typography>
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                              <Typography variant="caption" color="text.secondary" sx={{ wordBreak: 'break-all' }}>
                                {p.url}
                              </Typography>
                              <Tooltip title="Open page in new tab">
                                <IconButton
                                  size="small"
                                  component="a"
                                  href={p.url}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  sx={{ p: 0.2, color: 'text.disabled', '&:hover': { color: 'primary.main' } }}
                                >
                                  <OpenInNewIcon sx={{ fontSize: 13 }} />
                                </IconButton>
                              </Tooltip>
                            </Box>
                          </TableCell>
                          <TableCell>
                            {/* Interactive Complexity Tier Selector */}
                            <Select
                              size="small"
                              value={p.complexity.toLowerCase()}
                              onChange={(e) =>
                                handlePageComplexityOverride(
                                  idx,
                                  e.target.value as 'simple' | 'medium' | 'complex'
                                )
                              }
                              sx={{
                                fontSize: '0.8rem',
                                fontWeight: '800',
                                borderRadius: '8px',
                                '& .MuiSelect-select': { py: 0.6, px: 1 },
                              }}
                            >
                              <MenuItem value="simple" sx={{ fontWeight: '700', color: '#059669' }}>
                                Simple (1.0 hr)
                              </MenuItem>
                              <MenuItem value="medium" sx={{ fontWeight: '700', color: '#D97706' }}>
                                Medium (2.5 hrs)
                              </MenuItem>
                              <MenuItem value="complex" sx={{ fontWeight: '700', color: '#DC2626' }}>
                                Complex (5.5 hrs)
                              </MenuItem>
                            </Select>
                          </TableCell>
                          <TableCell align="center">
                            <Typography variant="body2" sx={{ fontWeight: '700' }}>
                              {p.manual_hours.toFixed(1)} hrs
                            </Typography>
                          </TableCell>
                          <TableCell align="center">
                            <Typography variant="body2">
                              ${p.manual_cost.toFixed(2)}
                            </Typography>
                          </TableCell>
                          <TableCell align="center">
                            <Typography variant="body2">
                              ${p.api_cost.toFixed(2)}
                            </Typography>
                          </TableCell>
                          <TableCell align="center">
                            <Typography variant="body2">
                              ${p.platform_cost.toFixed(2)}
                            </Typography>
                          </TableCell>
                          <TableCell align="right">
                            <Typography variant="body2" sx={{ color: '#059669', fontWeight: '600' }}>
                              ${p.base_cost.toFixed(2)}
                            </Typography>
                          </TableCell>
                          <TableCell align="right">
                            <Typography variant="body2" sx={{ color: '#059669', fontWeight: '600' }}>
                              ${p.profit_margin.toFixed(2)}
                            </Typography>
                          </TableCell>
                          <TableCell align="right">
                            <Typography variant="subtitle2" sx={{ fontWeight: '800', color: 'primary.main', fontSize: '0.95rem' }}>
                              ${p.final_cost.toFixed(2)}
                            </Typography>
                          </TableCell>
                          <TableCell align="center">
                            <IconButton
                              size="small"
                              onClick={() => toggleRow(idx)}
                              sx={{
                                transition: 'transform 0.2s',
                                transform: isExpanded ? 'rotate(180deg)' : 'none',
                              }}
                            >
                              <ExpandMoreIcon />
                            </IconButton>
                          </TableCell>
                        </TableRow>

                        {/* Expandable Evidence Row */}
                        <TableRow>
                          <TableCell colSpan={11} sx={{ py: 0, borderBottom: isExpanded ? undefined : 'none' }}>
                            <Collapse in={isExpanded} timeout="auto" unmountOnExit>
                              <Box sx={{ p: 3, bgcolor: '#F8FAFC', borderRadius: '12px', my: 1.5, border: '1px solid', borderColor: 'divider' }}>
                                <Grid container spacing={3} component="div">
                                  {/* Left: Identified Triggers */}
                                  <Grid size={{ xs: 12, md: 7 }} component="div">
                                    <Typography variant="subtitle2" sx={{ fontWeight: '800', mb: 1 }}>
                                      Detection Evidence & Complexity Triggers:
                                    </Typography>
                                    <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                                      {p.summary_rationale}
                                    </Typography>

                                    <Typography variant="caption" sx={{ fontWeight: '800', display: 'block', mb: 1, color: 'text.secondary' }}>
                                      ACTIVE TRIGGER FLAGS:
                                    </Typography>
                                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                                      {p.triggers.map((trig: string, tIdx: number) => (
                                        <Chip
                                          key={tIdx}
                                          icon={<CheckCircleIcon />}
                                          label={trig}
                                          size="small"
                                          variant="outlined"
                                          color={getComplexityColor(p.complexity)}
                                          sx={{ fontWeight: '600' }}
                                        />
                                      ))}
                                    </Box>
                                  </Grid>

                                  {/* Right: DOM Element Inventory Breakdown */}
                                  <Grid size={{ xs: 12, md: 5 }} component="div">
                                    <Typography variant="subtitle2" sx={{ fontWeight: '800', mb: 1 }}>
                                      DOM Element Inventory:
                                    </Typography>
                                    <Grid container spacing={1} component="div">
                                      {[
                                        { label: 'Total Elements', val: p.counts.total_elements },
                                        { label: 'Links (a[href])', val: p.counts.links },
                                        { label: 'Interactive Buttons', val: p.counts.buttons },
                                        { label: 'Headings (h1-h6)', val: p.counts.headings },
                                        { label: 'Form Controls', val: p.counts.inputs },
                                        { label: 'Media / Videos', val: p.counts.media },
                                        { label: 'Data Tables', val: p.counts.tables },
                                        { label: 'Images / Icons', val: p.counts.images },
                                      ].map((stat, sIdx) => (
                                        <Grid size={{ xs: 6 }} key={sIdx} component="div">
                                          <Box sx={{ p: 1, bgcolor: '#FFFFFF', borderRadius: '6px', border: '1px solid #E2E8F0' }}>
                                            <Typography variant="caption" color="text.secondary" sx={{ display: 'block' }}>
                                              {stat.label}
                                            </Typography>
                                            <Typography variant="subtitle2" sx={{ fontWeight: '800' }}>
                                              {stat.val}
                                            </Typography>
                                          </Box>
                                        </Grid>
                                      ))}
                                    </Grid>
                                  </Grid>
                                </Grid>
                              </Box>
                            </Collapse>
                          </TableCell>
                        </TableRow>
                      </React.Fragment>
                    );
                  })}
                </TableBody>

                {/* ── Table Footer: Logical Page-Wise Column Totals ── */}
                <TableFooter sx={{ bgcolor: '#F1F5F9', borderTop: '2px solid', borderColor: 'divider' }}>
                  <TableRow>
                    <TableCell sx={{ fontWeight: '800', color: 'primary.main' }}>Σ</TableCell>
                    <TableCell sx={{ fontWeight: '800', color: 'primary.main' }}>
                      TOTAL ({result.summary.total_pages} Pages)
                    </TableCell>
                    <TableCell>
                      <Typography variant="caption" sx={{ fontWeight: '700', color: 'text.secondary' }}>
                        {result.summary.simple_pages} Simple · {result.summary.medium_pages} Medium · {result.summary.complex_pages} Complex
                      </Typography>
                    </TableCell>
                    <TableCell align="center" sx={{ fontWeight: '800' }}>
                      {result.summary.total_manual_hours.toFixed(1)} hrs
                    </TableCell>
                    <TableCell align="center" sx={{ fontWeight: '800' }}>
                      ${result.summary.total_manual_cost.toFixed(2)}
                    </TableCell>
                    <TableCell align="center" sx={{ fontWeight: '800' }}>
                      ${result.summary.total_api_cost.toFixed(2)}
                    </TableCell>
                    <TableCell align="center" sx={{ fontWeight: '800' }}>
                      ${result.summary.total_platform_cost.toFixed(2)}
                    </TableCell>
                    <TableCell align="right" sx={{ fontWeight: '800', color: '#059669' }}>
                      ${result.summary.total_base_cost.toFixed(2)}
                    </TableCell>
                    <TableCell align="right" sx={{ fontWeight: '800', color: '#059669' }}>
                      ${result.summary.total_profit_margin.toFixed(2)}
                    </TableCell>
                    <TableCell align="right" sx={{ fontWeight: '800', color: 'primary.main', fontSize: '1.05rem' }}>
                      ${result.summary.total_final_cost.toFixed(2)}
                    </TableCell>
                    <TableCell />
                  </TableRow>
                </TableFooter>
              </Table>
            </TableContainer>
          </Card>
        </>
      )}
    </Box>
  );
};

export default EstimationPage;
