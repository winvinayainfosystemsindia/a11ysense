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
  TableRow,
  Paper,
  CircularProgress,
  Alert,
  InputAdornment,
  Divider,
  Collapse,
  IconButton
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

import {
  estimationService,
} from '../../service/estimationService';
import type {
  EstimationResult,
  EstimatedPage
} from '../../service/estimationService';

export const EstimationPage: React.FC = () => {
  const [url, setUrl] = useState('');
  const [depth, setDepth] = useState<number>(1);
  const [maxPages, setMaxPages] = useState<number>(10);
  const [hourlyRate, setHourlyRate] = useState<number>(40);
  const [platformFee, setPlatformFee] = useState<number>(10);
  const [profitMarginPct, setProfitMarginPct] = useState<number>(30);

  const [loading, setLoading] = useState(false);
  const [exportingExcel, setExportingExcel] = useState(false);
  const [exportingPdf, setExportingPdf] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<EstimationResult | null>(null);
  const [expandedRows, setExpandedRows] = useState<Record<number, boolean>>({});
  const [showCriteriaGuide, setShowCriteriaGuide] = useState(false);

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

  const handleAnalyze = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!url.trim()) return;

    setLoading(true);
    setError(null);

    try {
      const data = await estimationService.analyze({
        url: url.trim(),
        depth,
        max_pages: maxPages,
        hourly_rate: Number(hourlyRate),
        platform_fee: Number(platformFee),
        profit_margin_pct: Number(profitMarginPct)
      });
      setResult(data);
    } catch (err: any) {
      console.error('Estimation failed:', err);
      setError(err?.response?.data?.detail || err?.message || 'Failed to estimate website complexity.');
    } finally {
      setLoading(false);
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
        profit_margin_pct: Number(newMargin)
      });
      setResult(updated);
    } catch (err: any) {
      console.error('Recalculation error:', err);
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

  return (
    <Box sx={{ pb: 6 }}>
      {/* Page Header */}
      <Stack component="div" direction={{ xs: 'column', md: 'row' }} sx={{ justifyContent: 'space-between', alignItems: { xs: 'flex-start', md: 'center' }, mb: 4 }}>
        <Box>
          <Typography variant="h4" sx={{ fontWeight: '800', mb: 0.5, letterSpacing: '-0.5px' }}>
            Audit Estimation & Quotation
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Inspect website structure, evaluate Simple/Medium/Complex tiers, and compute quotes with 30% profit margin.
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

      {/* URL & Analysis Parameters Card */}
      <Card sx={{ mb: 4, borderRadius: '12px', border: '1px solid', borderColor: 'divider', boxShadow: 'none' }}>
        <CardContent sx={{ p: 3 }}>
          <form onSubmit={handleAnalyze}>
            <Grid container spacing={3} component="div" sx={{ alignItems: 'center' }}>
              <Grid size={{ xs: 12, md: 6 }} component="div">
                <TextField
                  fullWidth
                  label="Target Website URL"
                  placeholder="https://example.com"
                  value={url}
                  onChange={(e) => setUrl(e.target.value)}
                  required
                  slotProps={{
                    input: {
                      startAdornment: (
                        <InputAdornment position="start">
                          <LanguageIcon color="action" />
                        </InputAdornment>
                      )
                    }
                  }}
                  helperText="Enter a domain or specific page to inspect."
                />
              </Grid>

              <Grid size={{ xs: 6, md: 2 }} component="div">
                <TextField
                  fullWidth
                  select
                  label="Crawl Scope"
                  value={depth}
                  onChange={(e) => setDepth(Number(e.target.value))}
                  slotProps={{ select: { native: true } }}
                >
                  <option value={1}>Single Page (Depth 1)</option>
                  <option value={2}>Multi-Page (Depth 2)</option>
                  <option value={3}>Deep Crawl (Depth 3)</option>
                </TextField>
              </Grid>

              <Grid size={{ xs: 6, md: 2 }} component="div">
                <TextField
                  fullWidth
                  type="number"
                  label="Max Pages"
                  value={maxPages}
                  onChange={(e) => setMaxPages(Math.max(1, Number(e.target.value)))}
                  slotProps={{ htmlInput: { min: 1, max: 25 } }}
                  disabled={depth === 1}
                />
              </Grid>

              <Grid size={{ xs: 12, md: 2 }} component="div">
                <Button
                  type="submit"
                  variant="contained"
                  color="primary"
                  fullWidth
                  size="large"
                  disabled={loading || !url.trim()}
                  startIcon={loading ? <CircularProgress size={20} color="inherit" /> : <CalculateIcon />}
                  sx={{ py: 1.8, fontWeight: '700', borderRadius: '8px' }}
                >
                  {loading ? 'Analyzing...' : 'Calculate'}
                </Button>
              </Grid>
            </Grid>
          </form>

          {error && (
            <Alert severity="error" sx={{ mt: 2, borderRadius: '8px' }}>
              {error}
            </Alert>
          )}
        </CardContent>
      </Card>

      {/* Criteria Breakdown Guide Expander */}
      <Box sx={{ mb: 4 }}>
        <Button
          variant="text"
          startIcon={<InfoOutlinedIcon />}
          endIcon={showCriteriaGuide ? <ExpandLessIcon /> : <ExpandMoreIcon />}
          onClick={() => setShowCriteriaGuide(!showCriteriaGuide)}
          sx={{ fontWeight: '600', textTransform: 'none', color: 'text.secondary' }}
        >
          {showCriteriaGuide ? 'Hide Complexity Classification Rules' : 'View Complexity Classification Rules (Simple / Medium / Complex)'}
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
                        startAdornment: <InputAdornment position="start">$</InputAdornment>
                      }
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
                        startAdornment: <InputAdornment position="start">$</InputAdornment>
                      }
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
                        endAdornment: <InputAdornment position="end">%</InputAdornment>
                      }
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
                boxShadow: '0 8px 24px rgba(13, 27, 42, 0.15)'
              }}>
                <CardContent sx={{ p: 3 }}>
                  <Stack component="div" direction="row" spacing={1} sx={{ alignItems: 'center', mb: 1, opacity: 0.9 }}>
                    <MonetizationOnIcon />
                    <Typography variant="body2" sx={{ fontWeight: '700', textTransform: 'uppercase' }}>
                      Final Client Quote
                    </Typography>
                  </Stack>
                  <Typography variant="h3" sx={{ fontWeight: '800' }}>
                    ${result.summary.total_final_cost.toFixed(2)}
                  </Typography>
                  <Typography variant="caption" sx={{ opacity: 0.85, mt: 0.5, display: 'block' }}>
                    Includes {result.summary.profit_margin_pct}% profit margin
                  </Typography>
                </CardContent>
              </Card>
            </Grid>

            {/* Manual Verification Hours */}
            <Grid size={{ xs: 12, sm: 6, md: 3 }} component="div">
              <Card sx={{ borderRadius: '12px', border: '1px solid', borderColor: 'divider' }}>
                <CardContent sx={{ p: 3 }}>
                  <Stack component="div" direction="row" spacing={1} sx={{ alignItems: 'center', mb: 1, color: 'text.secondary' }}>
                    <AccessTimeIcon />
                    <Typography variant="body2" sx={{ fontWeight: '700', textTransform: 'uppercase' }}>
                      Manual Testing Effort
                    </Typography>
                  </Stack>
                  <Typography variant="h3" sx={{ fontWeight: '800', color: 'text.primary' }}>
                    {result.summary.total_manual_hours} <Typography component="span" variant="h5">hrs</Typography>
                  </Typography>
                  <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5, display: 'block' }}>
                    Cost: ${result.summary.total_manual_cost.toFixed(2)} (${result.summary.hourly_rate}/hr)
                  </Typography>
                </CardContent>
              </Card>
            </Grid>

            {/* Platform & API Base Cost */}
            <Grid size={{ xs: 12, sm: 6, md: 3 }} component="div">
              <Card sx={{ borderRadius: '12px', border: '1px solid', borderColor: 'divider' }}>
                <CardContent sx={{ p: 3 }}>
                  <Stack component="div" direction="row" spacing={1} sx={{ alignItems: 'center', mb: 1, color: 'text.secondary' }}>
                    <LayersIcon />
                    <Typography variant="body2" sx={{ fontWeight: '700', textTransform: 'uppercase' }}>
                      Base Production Cost
                    </Typography>
                  </Stack>
                  <Typography variant="h3" sx={{ fontWeight: '800', color: 'text.primary' }}>
                    ${result.summary.total_base_cost.toFixed(2)}
                  </Typography>
                  <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5, display: 'block' }}>
                    Platform: ${result.summary.total_platform_cost.toFixed(2)} | API: ${result.summary.total_api_cost.toFixed(2)}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>

            {/* Profit Margin */}
            <Grid size={{ xs: 12, sm: 6, md: 3 }} component="div">
              <Card sx={{ borderRadius: '12px', border: '1px solid', borderColor: 'divider' }}>
                <CardContent sx={{ p: 3 }}>
                  <Stack component="div" direction="row" spacing={1} sx={{ alignItems: 'center', mb: 1, color: 'success.main' }}>
                    <TrendingUpIcon />
                    <Typography variant="body2" sx={{ fontWeight: '700', textTransform: 'uppercase' }}>
                      Profit Margin ({result.summary.profit_margin_pct}%)
                    </Typography>
                  </Stack>
                  <Typography variant="h3" sx={{ fontWeight: '800', color: 'success.main' }}>
                    ${result.summary.total_profit_margin.toFixed(2)}
                  </Typography>
                  <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5, display: 'block' }}>
                    Net profit on this audit package
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
                    TOTAL PAGES SCANNED
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
                Page-by-Page Audit Line Items
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Detailed effort and cost computation per URL based on automated element inspection.
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
                  <TableCell align="center" sx={{ fontWeight: '800' }}>API Cost</TableCell>
                  <TableCell align="center" sx={{ fontWeight: '800' }}>Platform Fee</TableCell>
                  <TableCell align="right" sx={{ fontWeight: '800' }}>Base Cost</TableCell>
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
                            {p.manual_hours} hrs
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
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
                        <TableCell colSpan={9} sx={{ py: 0, borderBottom: isExpanded ? undefined : 'none' }}>
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
                                Links: {p.counts.links} | Buttons: {p.counts.buttons} | Headings: {p.counts.headings} | Paragraphs: {p.counts.paragraphs} | Forms: {p.counts.forms} | Inputs: {p.counts.inputs} | Tables: {p.counts.tables} | Media: {p.counts.media} | Total DOM Nodes: {p.counts.total_elements}
                              </Typography>
                            </Box>
                          </Collapse>
                        </TableCell>
                      </TableRow>
                    </React.Fragment>
                  );
                })}
              </TableBody>
            </Table>
          </TableContainer>
        </>
      )}
    </Box>
  );
};

export default EstimationPage;
