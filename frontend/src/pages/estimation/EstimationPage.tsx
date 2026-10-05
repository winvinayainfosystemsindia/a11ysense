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
  Checkbox
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

import {
  estimationService,
} from '../../service/estimationService';
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
    let urlsToAnalyze: string[] = [];

    if (inputMode === 0) {
      urlsToAnalyze = Object.keys(selectedUrls).filter((u) => selectedUrls[u]);
      if (urlsToAnalyze.length === 0) {
        setError('Please select at least one discovered URL to estimate.');
        return;
      }
    } else {
      urlsToAnalyze = parsedCustomUrls;
      if (urlsToAnalyze.length === 0) {
        setError('Please enter at least one URL to estimate.');
        return;
      }
    }

    setAnalyzing(true);
    setError(null);

    try {
      const data = await estimationService.analyze({
        urls: urlsToAnalyze,
        hourly_rate: Number(hourlyRate),
        platform_fee: Number(platformFee),
        profit_margin_pct: Number(profitMarginPct),
      });
      setResult(data);
    } catch (err: any) {
      console.error('Estimation failed:', err);
      setError(err?.response?.data?.detail || err?.message || 'Failed to estimate pages.');
    } finally {
      setAnalyzing(false);
    }
  };

  const handleRecalculate = async (
    newRate: number = hourlyRate,
    newFee: number = platformFee,
    newMargin: number = profitMarginPct
  ) => {
    if (!result || !result.pages.length) return;

    try {
      const updated = await estimationService.recalculate({
        pages: result.pages,
        hourly_rate: Number(newRate),
        platform_fee: Number(newFee),
        profit_margin_pct: Number(newMargin),
      });
      setResult(updated);
    } catch (err: any) {
      console.error('Recalculation error:', err);
    }
  };

  const handleDownloadExcel = async () => {
    if (!result) return;
    try {
      setExportingExcel(true);
      await estimationService.downloadQuotationExcel(result);
    } catch (err: any) {
      console.error('Failed to download Excel quotation:', err);
      setError('Failed to download Excel quotation report.');
    } finally {
      setExportingExcel(false);
    }
  };

  const handleDownloadPdf = async () => {
    if (!result) return;
    try {
      setExportingPdf(true);
      await estimationService.downloadQuotationPdf(result);
    } catch (err: any) {
      console.error('Failed to download PDF quotation:', err);
      setError('Failed to download PDF quotation report.');
    } finally {
      setExportingPdf(false);
    }
  };

  const toggleRow = (index: number) => {
    setExpandedRows((prev) => ({ ...prev, [index]: !prev[index] }));
  };

  const getComplexityColor = (complexity: string): 'success' | 'warning' | 'error' | 'default' => {
    switch (complexity?.toLowerCase()) {
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

  const filteredDiscoveredPages = discoveredPages.filter(
    (p) =>
      p.url.toLowerCase().includes(filterKeyword.toLowerCase()) ||
      p.path.toLowerCase().includes(filterKeyword.toLowerCase())
  );

  return (
    <Box sx={{ pb: 6 }}>
      {/* Page Header */}
      <Stack
        component="div"
        direction={{ xs: 'column', md: 'row' }}
        sx={{ justifyContent: 'space-between', alignItems: { xs: 'flex-start', md: 'center' }, mb: 4 }}
      >
        <Box>
          <Typography variant="h4" sx={{ fontWeight: '800', mb: 0.5, letterSpacing: '-0.5px' }}>
            Audit Estimation & Quotation
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Inspect page complexity, calculate manual effort & API usage, and generate executive commercial quotes.
          </Typography>
        </Box>
        {result && (
          <Stack component="div" direction={{ xs: 'column', sm: 'row' }} spacing={1.5} sx={{ mt: { xs: 2, md: 0 } }}>
            <Button
              variant="contained"
              color="success"
              startIcon={exportingExcel ? <CircularProgress size={18} color="inherit" /> : <FileDownloadIcon />}
              onClick={handleDownloadExcel}
              disabled={exportingExcel}
              sx={{ fontWeight: '700', borderRadius: '8px', textTransform: 'none', px: 2.5 }}
            >
              {exportingExcel ? 'Exporting...' : 'Download Quotation (Excel)'}
            </Button>
            <Button
              variant="outlined"
              color="primary"
              startIcon={exportingPdf ? <CircularProgress size={18} color="inherit" /> : <DescriptionIcon />}
              onClick={handleDownloadPdf}
              disabled={exportingPdf}
              sx={{ fontWeight: '700', borderRadius: '8px', textTransform: 'none', px: 2.5 }}
            >
              {exportingPdf ? 'Exporting...' : 'Download Proposal (PDF)'}
            </Button>
            <Button
              variant="outlined"
              color="inherit"
              startIcon={<PrintIcon />}
              onClick={() => window.print()}
              sx={{ fontWeight: '700', borderRadius: '8px', textTransform: 'none' }}
            >
              Print
            </Button>
          </Stack>
        )}
      </Stack>

      {/* Input Mode Selector Card */}
      <Card sx={{ mb: 4, borderRadius: '12px', border: '1px solid', borderColor: 'divider', boxShadow: 'none' }}>
        <Box sx={{ borderBottom: 1, borderColor: 'divider', bgcolor: 'rgba(0, 0, 0, 0.02)' }}>
          <Tabs
            value={inputMode}
            onChange={(_, val) => setInputMode(val)}
            textColor="primary"
            indicatorColor="primary"
            sx={{ px: 2 }}
          >
            <Tab
              icon={<TravelExploreIcon />}
              iconPosition="start"
              label="Discover from Base URL (Crawl & Select)"
              sx={{ fontWeight: '700', textTransform: 'none', py: 2 }}
            />
            <Tab
              icon={<LinkIcon />}
              iconPosition="start"
              label="Direct URL List (Client-Provided URLs)"
              sx={{ fontWeight: '700', textTransform: 'none', py: 2 }}
            />
          </Tabs>
        </Box>

        <CardContent sx={{ p: 3 }}>
          {/* Mode 0: Crawl & Discover from Base URL */}
          {inputMode === 0 && (
            <Box>
              <form onSubmit={handleDiscover}>
                <Grid container spacing={3} component="div" sx={{ alignItems: 'center' }}>
                  <Grid size={{ xs: 12, md: 6 }} component="div">
                    <TextField
                      fullWidth
                      label="Website Base URL"
                      placeholder="https://lemonn.co.in"
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
                      helperText="Enter root domain or section URL to discover internal pages."
                    />
                  </Grid>

                  <Grid size={{ xs: 6, md: 2 }} component="div">
                    <TextField
                      fullWidth
                      select
                      label="Crawl Scope"
                      value={discoveryDepth}
                      onChange={(e) => setDiscoveryDepth(Number(e.target.value))}
                      slotProps={{ select: { native: true } }}
                    >
                      <option value={1}>Level 1 (Nav & Home Links)</option>
                      <option value={2}>Level 2 (Internal Sub-pages)</option>
                      <option value={3}>Level 3 (Deep Discovery)</option>
                    </TextField>
                  </Grid>

                  <Grid size={{ xs: 6, md: 2 }} component="div">
                    <TextField
                      fullWidth
                      type="number"
                      label="Max Discovery"
                      value={maxDiscovery}
                      onChange={(e) => setMaxDiscovery(Math.max(5, Number(e.target.value)))}
                      slotProps={{ htmlInput: { min: 5, max: 100 } }}
                    />
                  </Grid>

                  <Grid size={{ xs: 12, md: 2 }} component="div">
                    <Button
                      type="submit"
                      variant="contained"
                      color="primary"
                      fullWidth
                      size="large"
                      disabled={discovering || !baseUrl.trim()}
                      startIcon={discovering ? <CircularProgress size={20} color="inherit" /> : <TravelExploreIcon />}
                      sx={{ py: 1.8, fontWeight: '700', borderRadius: '8px' }}
                    >
                      {discovering ? 'Discovering...' : 'Discover Pages'}
                    </Button>
                  </Grid>
                </Grid>
              </form>

              {/* Discovered URLs List / Selector */}
              {discoveredPages.length > 0 && (
                <Box sx={{ mt: 3.5, p: 2.5, bgcolor: 'background.default', borderRadius: '10px', border: '1px solid', borderColor: 'divider' }}>
                  <Stack
                    component="div"
                    direction={{ xs: 'column', sm: 'row' }}
                    sx={{ justifyContent: 'space-between', alignItems: { xs: 'flex-start', sm: 'center' }, mb: 2 }}
                  >
                    <Box>
                      <Typography variant="subtitle1" sx={{ fontWeight: '800' }}>
                        Discovered Pages ({discoveredPages.length})
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        Check the specific pages you wish to include in this audit quotation.
                      </Typography>
                    </Box>
                    <Stack component="div" direction="row" spacing={1} sx={{ mt: { xs: 1.5, sm: 0 }, alignItems: 'center' }}>
                      <TextField
                        size="small"
                        placeholder="Filter path/keyword..."
                        value={filterKeyword}
                        onChange={(e) => setFilterKeyword(e.target.value)}
                        slotProps={{
                          input: {
                            startAdornment: (
                              <InputAdornment position="start">
                                <SearchIcon fontSize="small" />
                              </InputAdornment>
                            ),
                          },
                        }}
                        sx={{ width: 220 }}
                      />
                      <Button size="small" variant="outlined" onClick={handleSelectAll} sx={{ fontWeight: '700', textTransform: 'none' }}>
                        Select All
                      </Button>
                      <Button size="small" variant="outlined" color="inherit" onClick={handleDeselectAll} sx={{ fontWeight: '700', textTransform: 'none' }}>
                        Deselect All
                      </Button>
                      <Chip
                        label={`${selectedCount} Selected`}
                        color={selectedCount > 0 ? 'primary' : 'default'}
                        sx={{ fontWeight: '800' }}
                      />
                    </Stack>
                  </Stack>

                  {/* Scrollable Checkbox Table */}
                  <TableContainer component={Paper} sx={{ maxHeight: 280, border: '1px solid', borderColor: 'divider', mb: 2 }}>
                    <Table size="small" stickyHeader>
                      <TableHead>
                        <TableRow>
                          <TableCell padding="checkbox" sx={{ bgcolor: 'background.paper', width: 48 }}>
                            <Checkbox
                              indeterminate={selectedCount > 0 && selectedCount < discoveredPages.length}
                              checked={discoveredPages.length > 0 && selectedCount === discoveredPages.length}
                              onChange={(e) => (e.target.checked ? handleSelectAll() : handleDeselectAll())}
                            />
                          </TableCell>
                          <TableCell sx={{ bgcolor: 'background.paper', fontWeight: '700' }}>URL Path</TableCell>
                          <TableCell sx={{ bgcolor: 'background.paper', fontWeight: '700' }}>Full Target URL</TableCell>
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
                              sx={{ cursor: 'pointer', bgcolor: isChecked ? 'rgba(25, 118, 210, 0.04)' : undefined }}
                            >
                              <TableCell padding="checkbox">
                                <Checkbox checked={isChecked} />
                              </TableCell>
                              <TableCell sx={{ fontWeight: '600', color: 'primary.main' }}>
                                {item.path}
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
                  <Stack component="div" direction={{ xs: 'column', sm: 'row' }} sx={{ justifyContent: 'space-between', alignItems: 'center' }}>
                    <Typography variant="body2" color="text.secondary">
                      {selectedCount === 0
                        ? 'Please select at least one page above.'
                        : `Ready to audit and estimate ${selectedCount} selected page(s).`}
                    </Typography>
                    <Button
                      variant="contained"
                      color="primary"
                      size="large"
                      onClick={handleAnalyzeSelected}
                      disabled={analyzing || selectedCount === 0}
                      startIcon={analyzing ? <CircularProgress size={20} color="inherit" /> : <CalculateIcon />}
                      sx={{ fontWeight: '800', px: 4, py: 1.5, borderRadius: '8px' }}
                    >
                      {analyzing ? 'Analyzing Complexity...' : `Calculate Estimation for (${selectedCount}) Pages`}
                    </Button>
                  </Stack>
                </Box>
              )}
            </Box>
          )}

          {/* Mode 1: Direct Custom URL List */}
          {inputMode === 1 && (
            <Box>
              <Typography variant="subtitle2" sx={{ fontWeight: '700', mb: 1 }}>
                Enter or Paste Client-Provided URLs (one URL per line or comma-separated):
              </Typography>
              <TextField
                fullWidth
                multiline
                rows={6}
                placeholder={`https://example.com/\nhttps://example.com/stocks\nhttps://example.com/ipo\nhttps://example.com/mutual-funds`}
                value={customUrlsText}
                onChange={(e) => setCustomUrlsText(e.target.value)}
                helperText="Enter each specific URL to audit on its own line. Full https:// domain paths are supported."
                sx={{ mb: 2 }}
              />

              <Stack component="div" direction={{ xs: 'column', sm: 'row' }} sx={{ justifyContent: 'space-between', alignItems: 'center' }}>
                <Chip
                  icon={<PlaylistAddCheckIcon />}
                  label={`${parsedCustomUrls.length} URL(s) Detected`}
                  color={parsedCustomUrls.length > 0 ? 'primary' : 'default'}
                  sx={{ fontWeight: '700' }}
                />

                <Button
                  variant="contained"
                  color="primary"
                  size="large"
                  onClick={handleAnalyzeSelected}
                  disabled={analyzing || parsedCustomUrls.length === 0}
                  startIcon={analyzing ? <CircularProgress size={20} color="inherit" /> : <CalculateIcon />}
                  sx={{ fontWeight: '800', px: 4, py: 1.5, borderRadius: '8px' }}
                >
                  {analyzing ? 'Analyzing Complexity...' : `Calculate Estimation for (${parsedCustomUrls.length}) Pages`}
                </Button>
              </Stack>
            </Box>
          )}
        </CardContent>
      </Card>

      {/* Error Banner */}
      {error && (
        <Alert severity="error" sx={{ mb: 4, borderRadius: '8px' }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* Classification Standards Guide Collapsible */}
      <Box sx={{ mb: 4 }}>
        <Button
          variant="text"
          color="inherit"
          onClick={() => setShowCriteriaGuide(!showCriteriaGuide)}
          startIcon={<InfoOutlinedIcon color="primary" />}
          endIcon={showCriteriaGuide ? <ExpandLessIcon /> : <ExpandMoreIcon />}
          sx={{ fontWeight: '700', textTransform: 'none', px: 0, mb: 1 }}
        >
          {showCriteriaGuide ? 'Hide Complexity Classification Rules' : 'View Complexity Classification Rules (Simple, Medium, Complex)'}
        </Button>

        <Collapse in={showCriteriaGuide}>
          <Grid container spacing={2} component="div" sx={{ mt: 1 }}>
            <Grid size={{ xs: 12, md: 4 }} component="div">
              <Card sx={{ bgcolor: 'rgba(46, 125, 50, 0.05)', border: '1px solid rgba(46, 125, 50, 0.2)', borderRadius: '10px' }}>
                <CardContent sx={{ p: 2 }}>
                  <Typography variant="subtitle1" sx={{ fontWeight: '700', color: 'success.main', mb: 1 }}>
                    Simple: Static Content Only (~1.0 Hr)
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    • Read top to bottom without interactive changes<br />
                    • Headings, paragraphs, and lists<br />
                    • Standard links (header, footer, basic navigation)<br />
                    • Plain buttons and decorative/informative images<br />
                    • <strong>Total links + buttons ≤ 60</strong>
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid size={{ xs: 12, md: 4 }} component="div">
              <Card sx={{ bgcolor: 'rgba(237, 108, 2, 0.05)', border: '1px solid rgba(237, 108, 2, 0.2)', borderRadius: '10px' }}>
                <CardContent sx={{ p: 2 }}>
                  <Typography variant="subtitle1" sx={{ fontWeight: '700', color: 'warning.main', mb: 1 }}>
                    Medium: Standard Interaction (~2.5 Hrs)
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    • Standard form (inputs, selects, checkboxes, submit)<br />
                    • Data tables with row and column headers<br />
                    • 1 embedded video, audio, map, or iframe<br />
                    • Expanding navigation (dropdowns, accordions, tabs)<br />
                    • Search input or <strong>total links/buttons &gt; 60</strong>
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid size={{ xs: 12, md: 4 }} component="div">
              <Card sx={{ bgcolor: 'rgba(211, 47, 47, 0.05)', border: '1px solid rgba(211, 47, 47, 0.2)', borderRadius: '10px' }}>
                <CardContent sx={{ p: 2 }}>
                  <Typography variant="subtitle1" sx={{ fontWeight: '700', color: 'error.main', mb: 1 }}>
                    Complex: Dynamic / Custom Widgets (~5.5 Hrs)
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    • Pop-up dialogs, cookie banners, chat widgets<br />
                    • Custom widgets (sliders, date pickers, trees, drag-drop)<br />
                    • Multi-step forms, sign-in/OTP/CAPTCHA, file upload<br />
                    • Carousels, live tickers, charts, or maps<br />
                    • Complex tables (merged cells, sortable columns)
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </Collapse>
      </Box>

      {/* Results Section */}
      {result && (
        <>
          {/* Rate Adjuster Strip */}
          <Card sx={{ mb: 4, bgcolor: 'background.paper', borderRadius: '12px', border: '1px solid', borderColor: 'divider' }}>
            <CardContent sx={{ p: 3 }}>
              <Typography variant="subtitle2" sx={{ fontWeight: '700', mb: 2, textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                Cost & Rate Configuration (Interactive)
              </Typography>
              <Grid container spacing={3} component="div" sx={{ alignItems: 'center' }}>
                <Grid size={{ xs: 12, sm: 4 }} component="div">
                  <TextField
                    fullWidth
                    size="small"
                    type="number"
                    label="Manual Testing Hourly Rate ($)"
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
                    helperText="NVDA / JAWS / Keyboard auditor rate"
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
                    helperText="Browser scanning & cloud compute"
                  />
                </Grid>
                <Grid size={{ xs: 12, sm: 4 }} component="div">
                  <TextField
                    fullWidth
                    size="small"
                    type="number"
                    label="Profit Margin (%)"
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
                    helperText="Client quotation markup"
                  />
                </Grid>
              </Grid>
            </CardContent>
          </Card>

          {/* KPI Cards */}
          <Grid container spacing={3} component="div" sx={{ mb: 4 }}>
            {/* Total Final Quote */}
            <Grid size={{ xs: 12, sm: 6, md: 3 }} component="div">
              <Card sx={{
                borderRadius: '12px',
                bgcolor: 'primary.main',
                color: 'primary.contrastText',
                boxShadow: '0 8px 24px rgba(13, 27, 42, 0.15)',
              }}>
                <CardContent sx={{ p: 3 }}>
                  <Stack component="div" direction="row" sx={{ justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                    <Typography variant="overline" sx={{ fontWeight: '700', letterSpacing: '1px', opacity: 0.85 }}>
                      FINAL QUOTED COST
                    </Typography>
                    <MonetizationOnIcon sx={{ opacity: 0.85 }} />
                  </Stack>
                  <Typography variant="h3" sx={{ fontWeight: '800' }}>
                    ${result.summary.total_final_cost.toFixed(2)}
                  </Typography>
                  <Typography variant="caption" sx={{ opacity: 0.8, mt: 0.5, display: 'block' }}>
                    Includes Base Cost + {result.summary.profit_margin_pct}% margin
                  </Typography>
                </CardContent>
              </Card>
            </Grid>

            {/* Total Manual Hours */}
            <Grid size={{ xs: 12, sm: 6, md: 3 }} component="div">
              <Card sx={{ borderRadius: '12px', border: '1px solid', borderColor: 'divider', boxShadow: 'none' }}>
                <CardContent sx={{ p: 3 }}>
                  <Stack component="div" direction="row" sx={{ justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                    <Typography variant="overline" color="text.secondary" sx={{ fontWeight: '700', letterSpacing: '1px' }}>
                      MANUAL EFFORT
                    </Typography>
                    <AccessTimeIcon color="action" />
                  </Stack>
                  <Typography variant="h3" sx={{ fontWeight: '800', color: 'primary.main' }}>
                    {result.summary.total_manual_hours.toFixed(1)} <Typography component="span" variant="h5" color="text.secondary">hrs</Typography>
                  </Typography>
                  <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5, display: 'block' }}>
                    ${result.summary.total_manual_cost.toFixed(2)} @ ${result.summary.hourly_rate}/hr
                  </Typography>
                </CardContent>
              </Card>
            </Grid>

            {/* Base Service Cost */}
            <Grid size={{ xs: 12, sm: 6, md: 3 }} component="div">
              <Card sx={{ borderRadius: '12px', border: '1px solid', borderColor: 'divider', boxShadow: 'none' }}>
                <CardContent sx={{ p: 3 }}>
                  <Stack component="div" direction="row" sx={{ justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                    <Typography variant="overline" color="text.secondary" sx={{ fontWeight: '700', letterSpacing: '1px' }}>
                      BASE SERVICE COST
                    </Typography>
                    <LayersIcon color="action" />
                  </Stack>
                  <Typography variant="h3" sx={{ fontWeight: '800' }}>
                    ${result.summary.total_base_cost.toFixed(2)}
                  </Typography>
                  <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5, display: 'block' }}>
                    Manual + API (${result.summary.total_api_cost.toFixed(2)}) + Platform (${result.summary.total_platform_cost.toFixed(2)})
                  </Typography>
                </CardContent>
              </Card>
            </Grid>

            {/* Total Profit Margin */}
            <Grid size={{ xs: 12, sm: 6, md: 3 }} component="div">
              <Card sx={{ borderRadius: '12px', border: '1px solid', borderColor: 'divider', boxShadow: 'none' }}>
                <CardContent sx={{ p: 3 }}>
                  <Stack component="div" direction="row" sx={{ justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                    <Typography variant="overline" color="text.secondary" sx={{ fontWeight: '700', letterSpacing: '1px' }}>
                      PROFIT MARKUP ({result.summary.profit_margin_pct}%)
                    </Typography>
                    <TrendingUpIcon color="success" />
                  </Stack>
                  <Typography variant="h3" sx={{ fontWeight: '800', color: 'success.main' }}>
                    ${result.summary.total_profit_margin.toFixed(2)}
                  </Typography>
                  <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5, display: 'block' }}>
                    Commercial quotation markup
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          </Grid>

          {/* Complexity Breakdown Badge Strip */}
          <Card sx={{ mb: 4, borderRadius: '12px', border: '1px solid', borderColor: 'divider' }}>
            <CardContent sx={{ p: 2.5 }}>
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
                  <Typography variant="caption" color="success.main" sx={{ fontWeight: '700' }}>
                    SIMPLE PAGES
                  </Typography>
                  <Typography variant="h5" sx={{ fontWeight: '800', color: 'success.main' }}>
                    {result.summary.simple_pages}
                  </Typography>
                </Box>
                <Divider orientation="vertical" flexItem />
                <Box sx={{ textAlign: 'center' }}>
                  <Typography variant="caption" color="warning.main" sx={{ fontWeight: '700' }}>
                    MEDIUM PAGES
                  </Typography>
                  <Typography variant="h5" sx={{ fontWeight: '800', color: 'warning.main' }}>
                    {result.summary.medium_pages}
                  </Typography>
                </Box>
                <Divider orientation="vertical" flexItem />
                <Box sx={{ textAlign: 'center' }}>
                  <Typography variant="caption" color="error.main" sx={{ fontWeight: '700' }}>
                    COMPLEX PAGES
                  </Typography>
                  <Typography variant="h5" sx={{ fontWeight: '800', color: 'error.main' }}>
                    {result.summary.complex_pages}
                  </Typography>
                </Box>
              </Stack>
            </CardContent>
          </Card>

          {/* Table Header Action Bar */}
          <Stack
            component="div"
            direction={{ xs: 'column', sm: 'row' }}
            sx={{ justifyContent: 'space-between', alignItems: { xs: 'flex-start', sm: 'center' }, mb: 2 }}
          >
            <Box>
              <Typography variant="h6" sx={{ fontWeight: '800' }}>
                Page-by-Page Audit Line Items & Logical Totals
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Itemized effort and cost breakdown per URL based on automated DOM inspection.
              </Typography>
            </Box>
            <Stack component="div" direction="row" spacing={1} sx={{ mt: { xs: 1.5, sm: 0 } }}>
              <Button
                size="small"
                variant="outlined"
                color="success"
                startIcon={exportingExcel ? <CircularProgress size={14} color="inherit" /> : <FileDownloadIcon />}
                onClick={handleDownloadExcel}
                disabled={exportingExcel}
                sx={{ fontWeight: '700', borderRadius: '6px', textTransform: 'none' }}
              >
                Excel Report
              </Button>
              <Button
                size="small"
                variant="outlined"
                color="primary"
                startIcon={exportingPdf ? <CircularProgress size={14} color="inherit" /> : <DescriptionIcon />}
                onClick={handleDownloadPdf}
                disabled={exportingPdf}
                sx={{ fontWeight: '700', borderRadius: '6px', textTransform: 'none' }}
              >
                PDF Report
              </Button>
            </Stack>
          </Stack>

          {/* Page-by-Page Detailed Quotation Table */}
          <TableContainer component={Paper} sx={{ borderRadius: '12px', border: '1px solid', borderColor: 'divider', boxShadow: 'none' }}>
            <Table>
              <TableHead sx={{ bgcolor: 'background.default' }}>
                <TableRow>
                  <TableCell sx={{ fontWeight: '800' }}>#</TableCell>
                  <TableCell sx={{ fontWeight: '800' }}>Page Details</TableCell>
                  <TableCell sx={{ fontWeight: '800' }}>Complexity Tier</TableCell>
                  <TableCell align="center" sx={{ fontWeight: '800' }}>Manual Effort</TableCell>
                  <TableCell align="center" sx={{ fontWeight: '800' }}>Manual Cost</TableCell>
                  <TableCell align="center" sx={{ fontWeight: '800' }}>API Cost</TableCell>
                  <TableCell align="center" sx={{ fontWeight: '800' }}>Platform Fee</TableCell>
                  <TableCell align="right" sx={{ fontWeight: '800' }}>Base Cost</TableCell>
                  <TableCell align="right" sx={{ fontWeight: '800' }}>Profit Margin</TableCell>
                  <TableCell align="right" sx={{ fontWeight: '800' }}>Final Cost (+30%)</TableCell>
                  <TableCell align="center" sx={{ fontWeight: '800' }}>Details</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {result.pages.map((p: EstimatedPage, idx: number) => {
                  const isExpanded = !!expandedRows[idx];
                  return (
                    <React.Fragment key={idx}>
                      <TableRow hover>
                        <TableCell sx={{ fontWeight: '600' }}>{idx + 1}</TableCell>
                        <TableCell sx={{ maxWidth: '300px' }}>
                          <Typography variant="subtitle2" noWrap sx={{ fontWeight: '700' }}>
                            {p.title}
                          </Typography>
                          <Typography variant="caption" color="text.secondary" sx={{ display: 'block', wordBreak: 'break-all' }}>
                            {p.url}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Chip
                            label={p.complexity_label.toUpperCase()}
                            color={getComplexityColor(p.complexity)}
                            size="small"
                            sx={{ fontWeight: '700' }}
                          />
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
                          <Typography variant="body2" color="text.secondary">
                            ${p.base_cost.toFixed(2)}
                          </Typography>
                        </TableCell>
                        <TableCell align="right">
                          <Typography variant="body2" sx={{ color: 'success.main', fontWeight: '600' }}>
                            ${p.profit_margin.toFixed(2)}
                          </Typography>
                        </TableCell>
                        <TableCell align="right">
                          <Typography variant="subtitle2" sx={{ fontWeight: '800', color: 'primary.main' }}>
                            ${p.final_cost.toFixed(2)}
                          </Typography>
                        </TableCell>
                        <TableCell align="center">
                          <IconButton size="small" onClick={() => toggleRow(idx)}>
                            {isExpanded ? <ExpandLessIcon /> : <ExpandMoreIcon />}
                          </IconButton>
                        </TableCell>
                      </TableRow>

                      {/* Expandable Evidence Row */}
                      <TableRow>
                        <TableCell colSpan={11} sx={{ py: 0, borderBottom: isExpanded ? undefined : 'none' }}>
                          <Collapse in={isExpanded} timeout="auto" unmountOnExit>
                            <Box sx={{ p: 2.5, bgcolor: 'rgba(0, 0, 0, 0.02)', borderRadius: '8px', my: 1 }}>
                              <Typography variant="subtitle2" sx={{ fontWeight: '700', mb: 1 }}>
                                Detection Evidence & Rationale:
                              </Typography>
                              <Typography variant="body2" color="text.secondary" sx={{ mb: 1.5 }}>
                                {p.summary_rationale}
                              </Typography>

                              <Typography variant="caption" sx={{ fontWeight: '700', display: 'block', mb: 0.5 }}>
                                SPECIFIC TRIGGERS IDENTIFIED:
                              </Typography>
                              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mb: 2 }}>
                                {p.triggers.map((trig: string, tIdx: number) => (
                                  <Chip
                                    key={tIdx}
                                    icon={<CheckCircleIcon />}
                                    label={trig}
                                    size="small"
                                    variant="outlined"
                                    color={getComplexityColor(p.complexity)}
                                    sx={{ my: 0.2 }}
                                  />
                                ))}
                              </Box>

                              <Typography variant="caption" sx={{ fontWeight: '700', display: 'block', mb: 0.5 }}>
                                ELEMENT COUNTS:
                              </Typography>
                              <Typography variant="caption" color="text.secondary">
                                Links: {p.counts.links} | Buttons: {p.counts.buttons} | Headings: {p.counts.headings} | Paragraphs: {p.counts.paragraphs} | Lists: {p.counts.lists} | Images: {p.counts.images} | Forms: {p.counts.forms} | Inputs: {p.counts.inputs} | Tables: {p.counts.tables} | Media: {p.counts.media} | Total DOM Nodes: {p.counts.total_elements}
                              </Typography>
                            </Box>
                          </Collapse>
                        </TableCell>
                      </TableRow>
                    </React.Fragment>
                  );
                })}
              </TableBody>

              {/* Bottom Logical Summary Footer Row */}
              <TableFooter sx={{ bgcolor: 'rgba(25, 118, 210, 0.06)' }}>
                <TableRow>
                  <TableCell sx={{ fontWeight: '800' }}>TOTAL</TableCell>
                  <TableCell sx={{ fontWeight: '800' }}>
                    {result.summary.total_pages} Page(s) Total
                  </TableCell>
                  <TableCell>
                    <Typography variant="caption" sx={{ fontWeight: '700', display: 'block' }}>
                      {result.summary.simple_pages} Simple | {result.summary.medium_pages} Med | {result.summary.complex_pages} Cmplx
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
                  <TableCell align="right" sx={{ fontWeight: '800' }}>
                    ${result.summary.total_base_cost.toFixed(2)}
                  </TableCell>
                  <TableCell align="right" sx={{ fontWeight: '800', color: 'success.main' }}>
                    ${result.summary.total_profit_margin.toFixed(2)}
                  </TableCell>
                  <TableCell align="right" sx={{ fontWeight: '800', color: 'primary.main', fontSize: '1rem' }}>
                    ${result.summary.total_final_cost.toFixed(2)}
                  </TableCell>
                  <TableCell />
                </TableRow>
              </TableFooter>
            </Table>
          </TableContainer>
        </>
      )}
    </Box>
  );
};

export default EstimationPage;
