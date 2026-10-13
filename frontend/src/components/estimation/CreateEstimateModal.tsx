import React, { useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Stepper,
  Step,
  StepLabel,
  Box,
  Typography,
  TextField,
  Button,
  Stack,
  Card,
  CardActionArea,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Checkbox,
  Paper,
  Chip,
  InputAdornment,
  CircularProgress,
  Alert,
  useTheme,
} from '@mui/material';
import Grid from '@mui/material/Grid';
import { alpha } from '@mui/material/styles';
import LanguageIcon from '@mui/icons-material/Language';
import ListAltIcon from '@mui/icons-material/ListAlt';
import SearchIcon from '@mui/icons-material/Search';
import TravelExploreIcon from '@mui/icons-material/TravelExplore';
import AttachMoneyIcon from '@mui/icons-material/AttachMoney';
import PlaylistAddCheckIcon from '@mui/icons-material/PlaylistAddCheck';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import CloseIcon from '@mui/icons-material/Close';
import IconButton from '@mui/material/IconButton';

import { estimationService } from '../../service/estimationService';
import type { DiscoveredUrlItem } from '../../service/estimationService';

interface CreateEstimateModalProps {
  open: boolean;
  onClose: () => void;
  onSuccess: (estimateId: string) => void;
  orgId?: string;
}

const STEPS = ['Mode & Details', 'Select URLs', 'Commercial Rates', 'Review & Run'];

export const CreateEstimateModal: React.FC<CreateEstimateModalProps> = ({
  open,
  onClose,
  onSuccess,
  orgId,
}) => {
  const theme = useTheme();
  const [activeStep, setActiveStep] = useState(0);

  // Step 1: Mode & Title
  const [title, setTitle] = useState('Website Audit Estimation');
  const [mode, setMode] = useState<'discover' | 'custom_urls'>('discover');

  // Step 2: URL Discovery / Input
  const [baseUrl, setBaseUrl] = useState('');
  const [discoveryDepth, setDiscoveryDepth] = useState<number>(1);
  const [maxDiscovery, setMaxDiscovery] = useState<number>(30);
  const [discovering, setDiscovering] = useState(false);
  const [discoveredPages, setDiscoveredPages] = useState<DiscoveredUrlItem[]>([]);
  const [selectedUrls, setSelectedUrls] = useState<Record<string, boolean>>({});
  const [filterKeyword, setFilterKeyword] = useState('');

  // Mode B: Custom URLs text
  const [customUrlsText, setCustomUrlsText] = useState('');

  // Step 3: Commercial Rates
  const [hourlyRate, setHourlyRate] = useState<number>(40);
  const [platformFee, setPlatformFee] = useState<number>(10);
  const [profitMarginPct, setProfitMarginPct] = useState<number>(30);

  // Step 4: Run state
  const [analyzing, setAnalyzing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Helper for custom URLs parsing
  const getParsedCustomUrls = (): string[] => {
    return customUrlsText
      .split(/[\n,]+/)
      .map((u) => u.trim())
      .filter((u) => u.length > 0);
  };

  const selectedCount = Object.values(selectedUrls).filter(Boolean).length;
  const parsedCustomCount = getParsedCustomUrls().length;

  const filteredDiscoveredPages = discoveredPages.filter((item) => {
    if (!filterKeyword) return true;
    const k = filterKeyword.toLowerCase();
    const titleMatch = (item.title || '').toLowerCase().includes(k);
    const pathMatch = (item.path || '').toLowerCase().includes(k);
    return titleMatch || pathMatch || item.url.toLowerCase().includes(k);
  });

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

  const getTargetUrls = (): string[] => {
    if (mode === 'discover') {
      return Object.entries(selectedUrls)
        .filter(([_, isSelected]) => isSelected)
        .map(([url]) => url);
    }
    return getParsedCustomUrls();
  };

  const handleNext = () => {
    setError(null);
    if (activeStep === 0) {
      if (!title.trim()) {
        setError('Please provide an estimation title.');
        return;
      }
    } else if (activeStep === 1) {
      const targets = getTargetUrls();
      if (targets.length === 0) {
        setError(
          mode === 'discover'
            ? 'Please discover and select at least one URL.'
            : 'Please enter at least one valid URL.'
        );
        return;
      }
    }
    setActiveStep((prev) => prev + 1);
  };

  const handleBack = () => {
    setError(null);
    setActiveStep((prev) => prev - 1);
  };

  const handleRunEstimation = async () => {
    const targetUrls = getTargetUrls();
    if (targetUrls.length === 0) {
      setError('Please select or input at least one target URL.');
      return;
    }

    setAnalyzing(true);
    setError(null);
    try {
      const primaryBase =
        mode === 'discover' && baseUrl.trim()
          ? baseUrl.trim()
          : targetUrls[0] || 'https://example.com';

      const result = await estimationService.analyze({
        urls: targetUrls,
        hourly_rate: hourlyRate,
        platform_fee: platformFee,
        profit_margin_pct: profitMarginPct,
        title: title.trim(),
        base_url: primaryBase,
        mode: mode,
        save_to_db: true,
        org_id: orgId,
      });

      if (result.id) {
        onSuccess(result.id);
      } else {
        // Fallback: manually save if not returned
        const saved = await estimationService.save({
          title: title.trim(),
          base_url: primaryBase,
          mode: mode,
          hourly_rate: hourlyRate,
          platform_fee: platformFee,
          profit_margin_pct: profitMarginPct,
          pages: result.pages,
          summary: result.summary,
          org_id: orgId,
        });
        onSuccess(saved.id);
      }
    } catch (err: any) {
      console.error('Estimation run failed:', err);
      setError(err?.response?.data?.detail || err?.message || 'Failed to execute estimation.');
      setAnalyzing(false);
    }
  };

  const handleResetAndClose = () => {
    if (analyzing) return;
    setActiveStep(0);
    setError(null);
    onClose();
  };

  return (
    <Dialog
      open={open}
      onClose={handleResetAndClose}
      maxWidth="md"
      fullWidth
      slotProps={{
        paper: {
          sx: {
            borderRadius: 3,
            p: 1,
            maxHeight: '92vh',
          },
        },
      }}
    >
      <DialogTitle sx={{ m: 0, p: 2.5, pb: 1.5, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Box>
          <Typography variant="h6" sx={{ fontWeight: 800 }}>
            Create Audit Estimation
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Configure target URLs, inspect DOM complexities, and calculate commercial quotes.
          </Typography>
        </Box>
        <IconButton onClick={handleResetAndClose} size="small" disabled={analyzing}>
          <CloseIcon />
        </IconButton>
      </DialogTitle>

      <Box sx={{ px: 3, pt: 1, pb: 2 }}>
        <Stepper activeStep={activeStep} alternativeLabel>
          {STEPS.map((label) => (
            <Step key={label}>
              <StepLabel>{label}</StepLabel>
            </Step>
          ))}
        </Stepper>
      </Box>

      <DialogContent dividers sx={{ p: 3 }}>
        {error && (
          <Alert severity="error" sx={{ mb: 3, borderRadius: 2 }} onClose={() => setError(null)}>
            {error}
          </Alert>
        )}

        {/* ── STEP 0: MODE & DETAILS ── */}
        {activeStep === 0 && (
          <Box>
            <Typography variant="subtitle2" sx={{ fontWeight: 700, mb: 1, color: 'text.secondary' }}>
              ESTIMATION TITLE
            </Typography>
            <TextField
              fullWidth
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="e.g. WinVinaya Corporate Portal Accessibility Audit"
              sx={{ mb: 3 }}
            />

            <Typography variant="subtitle2" sx={{ fontWeight: 700, mb: 1.5, color: 'text.secondary' }}>
              CHOOSE DISCOVERY MODE
            </Typography>

            <Grid container spacing={2.5} component="div">
              <Grid size={{ xs: 12, sm: 6 }} component="div">
                <Card
                  variant="outlined"
                  sx={{
                    borderRadius: 3,
                    borderColor: mode === 'discover' ? theme.palette.primary.main : theme.palette.divider,
                    borderWidth: mode === 'discover' ? 2 : 1,
                    bgcolor: mode === 'discover' ? alpha(theme.palette.primary.main, 0.04) : 'background.paper',
                    transition: 'all 0.2s ease',
                  }}
                >
                  <CardActionArea onClick={() => setMode('discover')} sx={{ p: 2.5 }}>
                    <Stack component="div" direction="row" spacing={1.5} sx={{ alignItems: 'center', mb: 1 }}>
                      <TravelExploreIcon color={mode === 'discover' ? 'primary' : 'action'} />
                      <Typography variant="h6" sx={{ fontWeight: 700, fontSize: '1.05rem' }}>
                        Discover from Website
                      </Typography>
                    </Stack>
                    <Typography variant="body2" color="text.secondary">
                      Provide a base URL to automatically crawl internal routes, extract page titles, and select target pages.
                    </Typography>
                  </CardActionArea>
                </Card>
              </Grid>

              <Grid size={{ xs: 12, sm: 6 }} component="div">
                <Card
                  variant="outlined"
                  sx={{
                    borderRadius: 3,
                    borderColor: mode === 'custom_urls' ? theme.palette.primary.main : theme.palette.divider,
                    borderWidth: mode === 'custom_urls' ? 2 : 1,
                    bgcolor: mode === 'custom_urls' ? alpha(theme.palette.primary.main, 0.04) : 'background.paper',
                    transition: 'all 0.2s ease',
                  }}
                >
                  <CardActionArea onClick={() => setMode('custom_urls')} sx={{ p: 2.5 }}>
                    <Stack component="div" direction="row" spacing={1.5} sx={{ alignItems: 'center', mb: 1 }}>
                      <ListAltIcon color={mode === 'custom_urls' ? 'primary' : 'action'} />
                      <Typography variant="h6" sx={{ fontWeight: 700, fontSize: '1.05rem' }}>
                        Direct URL List
                      </Typography>
                    </Stack>
                    <Typography variant="body2" color="text.secondary">
                      Paste or enter a specific list of target URLs provided directly by your client or product team.
                    </Typography>
                  </CardActionArea>
                </Card>
              </Grid>
            </Grid>
          </Box>
        )}

        {/* ── STEP 1: URL SELECTION ── */}
        {activeStep === 1 && (
          <Box>
            {mode === 'discover' ? (
              <Box>
                {/* Discovery configuration */}
                <form onSubmit={handleDiscover}>
                  <Grid container spacing={2} component="div" sx={{ alignItems: 'flex-start', mb: 2 }}>
                    <Grid size={{ xs: 12, sm: 6 }} component="div">
                      <Typography variant="caption" sx={{ fontWeight: 700, color: 'text.secondary', display: 'block', mb: 0.5 }}>
                        BASE ROOT URL
                      </Typography>
                      <TextField
                        fullWidth
                        size="small"
                        placeholder="https://example.com"
                        value={baseUrl}
                        onChange={(e) => setBaseUrl(e.target.value)}
                        slotProps={{
                          input: {
                            startAdornment: (
                              <InputAdornment position="start">
                                <LanguageIcon fontSize="small" color="action" />
                              </InputAdornment>
                            ),
                          },
                        }}
                      />
                    </Grid>

                    <Grid size={{ xs: 6, sm: 3 }} component="div">
                      <Typography variant="caption" sx={{ fontWeight: 700, color: 'text.secondary', display: 'block', mb: 0.5 }}>
                        CRAWL DEPTH
                      </Typography>
                      <TextField
                        fullWidth
                        size="small"
                        select
                        value={discoveryDepth}
                        onChange={(e) => setDiscoveryDepth(Number(e.target.value))}
                        slotProps={{ select: { native: true } }}
                      >
                        <option value={1}>Level 1 (Direct Links)</option>
                        <option value={2}>Level 2 (Sub-pages)</option>
                        <option value={3}>Level 3 (Deep)</option>
                      </TextField>
                    </Grid>

                    <Grid size={{ xs: 6, sm: 3 }} component="div">
                      <Typography variant="caption" sx={{ fontWeight: 700, color: 'text.secondary', display: 'block', mb: 0.5 }}>
                        MAX PAGES
                      </Typography>
                      <TextField
                        fullWidth
                        size="small"
                        type="number"
                        value={maxDiscovery}
                        onChange={(e) => setMaxDiscovery(Math.min(100, Math.max(1, Number(e.target.value))))}
                        slotProps={{ htmlInput: { min: 1, max: 100 } }}
                      />
                    </Grid>
                  </Grid>

                  <Stack component="div" direction="row" spacing={1.5} sx={{ mb: 2, alignItems: 'center' }}>
                    <Button
                      variant="contained"
                      color="primary"
                      onClick={() => handleDiscover()}
                      disabled={discovering || !baseUrl.trim()}
                      startIcon={discovering ? <CircularProgress size={16} color="inherit" /> : <TravelExploreIcon />}
                      sx={{ fontWeight: 700, textTransform: 'none' }}
                    >
                      {discovering ? 'Discovering Pages...' : 'Discover Pages'}
                    </Button>

                    {/* Presets */}
                    <Chip
                      label="WinVinaya.com"
                      size="small"
                      clickable
                      onClick={() => setBaseUrl('https://winvinaya.com')}
                      sx={{ fontWeight: 600 }}
                    />
                    <Chip
                      label="Lemonn.co.in"
                      size="small"
                      clickable
                      onClick={() => setBaseUrl('https://lemonn.co.in')}
                      sx={{ fontWeight: 600 }}
                    />
                  </Stack>
                </form>

                {/* Discovered URLs Table (NO ROUTE PATH COLUMN: Page Title & Full URL only) */}
                {discoveredPages.length > 0 && (
                  <Box sx={{ mt: 2.5 }}>
                    <Stack
                      component="div"
                      direction={{ xs: 'column', sm: 'row' }}
                      spacing={1.5}
                      sx={{ justifyContent: 'space-between', alignItems: { xs: 'flex-start', sm: 'center' }, mb: 1.5 }}
                    >
                      <Stack component="div" direction="row" spacing={1} sx={{ alignItems: 'center' }}>
                        <PlaylistAddCheckIcon color="primary" fontSize="small" />
                        <Typography variant="subtitle2" sx={{ fontWeight: 800 }}>
                          Discovered URLs ({discoveredPages.length})
                        </Typography>
                        <Chip
                          label={`${selectedCount} Selected`}
                          size="small"
                          color={selectedCount > 0 ? 'primary' : 'default'}
                          sx={{ fontWeight: 700 }}
                        />
                      </Stack>

                      <Stack component="div" direction="row" spacing={1} sx={{ alignItems: 'center' }}>
                        <TextField
                          size="small"
                          placeholder="Filter URLs or title..."
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
                          sx={{ width: { xs: '100%', sm: 200 } }}
                        />
                        <Button size="small" variant="outlined" onClick={handleSelectAll} sx={{ textTransform: 'none', fontWeight: 700 }}>
                          Select All
                        </Button>
                        <Button size="small" variant="outlined" color="inherit" onClick={handleDeselectAll} sx={{ textTransform: 'none', fontWeight: 700 }}>
                          Deselect All
                        </Button>
                      </Stack>
                    </Stack>

                    <TableContainer
                      component={Paper}
                      sx={{
                        maxHeight: 280,
                        border: '1px solid',
                        borderColor: theme.palette.divider,
                        borderRadius: 2,
                        boxShadow: 'none',
                      }}
                    >
                      <Table size="small" stickyHeader>
                        <TableHead>
                          <TableRow>
                            <TableCell padding="checkbox" sx={{ bgcolor: theme.palette.grey[100], width: 44 }}>
                              <Checkbox
                                indeterminate={selectedCount > 0 && selectedCount < discoveredPages.length}
                                checked={discoveredPages.length > 0 && selectedCount === discoveredPages.length}
                                onChange={(e) => (e.target.checked ? handleSelectAll() : handleDeselectAll())}
                              />
                            </TableCell>
                            <TableCell sx={{ bgcolor: theme.palette.grey[100], fontWeight: 800, width: 260 }}>
                              Page Title
                            </TableCell>
                            <TableCell sx={{ bgcolor: theme.palette.grey[100], fontWeight: 800 }}>
                              Full Target URL
                            </TableCell>
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
                                  bgcolor: isChecked ? alpha(theme.palette.primary.main, 0.05) : undefined,
                                }}
                              >
                                <TableCell padding="checkbox">
                                  <Checkbox checked={isChecked} />
                                </TableCell>
                                <TableCell sx={{ fontWeight: 600, color: 'text.primary', fontSize: '0.88rem' }}>
                                  {item.title || item.path || 'Page'}
                                </TableCell>
                                <TableCell sx={{ color: 'text.secondary', fontSize: '0.84rem', wordBreak: 'break-all' }}>
                                  {item.url}
                                </TableCell>
                              </TableRow>
                            );
                          })}
                        </TableBody>
                      </Table>
                    </TableContainer>
                  </Box>
                )}
              </Box>
            ) : (
              <Box>
                <Typography variant="caption" sx={{ fontWeight: 700, color: 'text.secondary', display: 'block', mb: 0.75 }}>
                  ENTER ONE URL PER LINE
                </Typography>
                <TextField
                  fullWidth
                  multiline
                  rows={8}
                  placeholder={`https://example.com/\nhttps://example.com/about\nhttps://example.com/contact`}
                  value={customUrlsText}
                  onChange={(e) => setCustomUrlsText(e.target.value)}
                  sx={{ mb: 2, fontFamily: 'Consolas, monospace' }}
                />

                <Stack component="div" direction="row" spacing={1.5} sx={{ alignItems: 'center' }}>
                  <Typography variant="caption" sx={{ fontWeight: 700, color: 'text.secondary' }}>
                    QUICK SAMPLES:
                  </Typography>
                  <Chip
                    label="WinVinaya 3 Pages"
                    size="small"
                    clickable
                    onClick={() =>
                      setCustomUrlsText(
                        'https://winvinaya.com\nhttps://winvinaya.com/about-us/\nhttps://winvinaya.com/contact-us/'
                      )
                    }
                    sx={{ fontWeight: 600 }}
                  />
                  <Chip
                    label="Lemonn 3 Pages"
                    size="small"
                    clickable
                    onClick={() =>
                      setCustomUrlsText(
                        'https://lemonn.co.in/\nhttps://lemonn.co.in/ipo\nhttps://lemonn.co.in/mutual-funds'
                      )
                    }
                    sx={{ fontWeight: 600 }}
                  />
                  <Typography variant="body2" color="primary" sx={{ fontWeight: 700, ml: 'auto' }}>
                    {parsedCustomCount} URL(s) detected
                  </Typography>
                </Stack>
              </Box>
            )}
          </Box>
        )}

        {/* ── STEP 2: COMMERCIAL RATES ── */}
        {activeStep === 2 && (
          <Box>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
              Set commercial pricing multipliers for manual assistive tech audits, automated scanning platform fees, and target business profit margin.
            </Typography>

            <Grid container spacing={3} component="div">
              <Grid size={{ xs: 12, md: 4 }} component="div">
                <Card variant="outlined" sx={{ p: 2.5, borderRadius: 3 }}>
                  <Typography variant="caption" sx={{ fontWeight: 700, color: 'text.secondary', display: 'block', mb: 1 }}>
                    MANUAL AUDITOR RATE ($/HR)
                  </Typography>
                  <TextField
                    fullWidth
                    type="number"
                    value={hourlyRate}
                    onChange={(e) => setHourlyRate(Math.max(0, Number(e.target.value)))}
                    slotProps={{
                      input: {
                        startAdornment: (
                          <InputAdornment position="start">
                            <AttachMoneyIcon fontSize="small" />
                          </InputAdornment>
                        ),
                      },
                    }}
                    helperText="Default standard: $40.00 / hr"
                  />
                </Card>
              </Grid>

              <Grid size={{ xs: 12, md: 4 }} component="div">
                <Card variant="outlined" sx={{ p: 2.5, borderRadius: 3 }}>
                  <Typography variant="caption" sx={{ fontWeight: 700, color: 'text.secondary', display: 'block', mb: 1 }}>
                    PLATFORM FEE ($/PAGE)
                  </Typography>
                  <TextField
                    fullWidth
                    type="number"
                    value={platformFee}
                    onChange={(e) => setPlatformFee(Math.max(0, Number(e.target.value)))}
                    slotProps={{
                      input: {
                        startAdornment: (
                          <InputAdornment position="start">
                            <AttachMoneyIcon fontSize="small" />
                          </InputAdornment>
                        ),
                      },
                    }}
                    helperText="Default scanning: $10.00 / page"
                  />
                </Card>
              </Grid>

              <Grid size={{ xs: 12, md: 4 }} component="div">
                <Card variant="outlined" sx={{ p: 2.5, borderRadius: 3 }}>
                  <Typography variant="caption" sx={{ fontWeight: 700, color: 'text.secondary', display: 'block', mb: 1 }}>
                    PROFIT MARGIN (%)
                  </Typography>
                  <TextField
                    fullWidth
                    type="number"
                    value={profitMarginPct}
                    onChange={(e) => setProfitMarginPct(Math.max(0, Number(e.target.value)))}
                    slotProps={{
                      input: {
                        endAdornment: <InputAdornment position="end">%</InputAdornment>,
                      },
                    }}
                    helperText="Default markup: 30%"
                  />
                </Card>
              </Grid>
            </Grid>
          </Box>
        )}

        {/* ── STEP 3: REVIEW & RUN ── */}
        {activeStep === 3 && (
          <Box>
            {analyzing ? (
              <Box sx={{ py: 6, textAlign: 'center' }}>
                <CircularProgress size={48} sx={{ mb: 2 }} />
                <Typography variant="h6" sx={{ fontWeight: 800, mb: 1 }}>
                  Running Headless DOM Complexity Analysis...
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ maxWidth: 500, mx: 'auto' }}>
                  Inspecting buttons, links, forms, tables, and media elements across all selected pages to classify WCAG complexity profiles and save to database.
                </Typography>
              </Box>
            ) : (
              <Box>
                <Typography variant="h6" sx={{ fontWeight: 800, mb: 2 }}>
                  Ready to Run Estimation
                </Typography>

                <Paper variant="outlined" sx={{ p: 3, borderRadius: 3, mb: 3 }}>
                  <Grid container spacing={2} component="div">
                    <Grid size={{ xs: 12, sm: 6 }} component="div">
                      <Typography variant="caption" color="text.secondary">
                        ESTIMATION TITLE
                      </Typography>
                      <Typography variant="subtitle1" sx={{ fontWeight: 700 }}>
                        {title}
                      </Typography>
                    </Grid>

                    <Grid size={{ xs: 12, sm: 6 }} component="div">
                      <Typography variant="caption" color="text.secondary">
                        DISCOVERY MODE
                      </Typography>
                      <Typography variant="subtitle1" sx={{ fontWeight: 700 }}>
                        {mode === 'discover' ? 'Crawl & Discover from Website' : 'Direct URL List'}
                      </Typography>
                    </Grid>

                    <Grid size={{ xs: 6, sm: 3 }} component="div">
                      <Typography variant="caption" color="text.secondary">
                        TARGET PAGES
                      </Typography>
                      <Typography variant="h6" color="primary" sx={{ fontWeight: 800 }}>
                        {getTargetUrls().length} Pages
                      </Typography>
                    </Grid>

                    <Grid size={{ xs: 6, sm: 3 }} component="div">
                      <Typography variant="caption" color="text.secondary">
                        AUDITOR RATE
                      </Typography>
                      <Typography variant="h6" sx={{ fontWeight: 800 }}>
                        ${hourlyRate}/hr
                      </Typography>
                    </Grid>

                    <Grid size={{ xs: 6, sm: 3 }} component="div">
                      <Typography variant="caption" color="text.secondary">
                        PLATFORM FEE
                      </Typography>
                      <Typography variant="h6" sx={{ fontWeight: 800 }}>
                        ${platformFee}/page
                      </Typography>
                    </Grid>

                    <Grid size={{ xs: 6, sm: 3 }} component="div">
                      <Typography variant="caption" color="text.secondary">
                        PROFIT MARGIN
                      </Typography>
                      <Typography variant="h6" sx={{ fontWeight: 800 }}>
                        {profitMarginPct}%
                      </Typography>
                    </Grid>
                  </Grid>
                </Paper>

                <Alert severity="info" sx={{ borderRadius: 2 }}>
                  Upon completion, this estimation will be saved to your PostgreSQL database with complete DOM inventories, complexity triggers, and proposal reports.
                </Alert>
              </Box>
            )}
          </Box>
        )}
      </DialogContent>

      <DialogActions sx={{ px: 3, py: 2 }}>
        <Button onClick={handleResetAndClose} disabled={analyzing} color="inherit">
          Cancel
        </Button>
        {activeStep > 0 && (
          <Button onClick={handleBack} disabled={analyzing} variant="outlined">
            Back
          </Button>
        )}
        {activeStep < STEPS.length - 1 ? (
          <Button onClick={handleNext} variant="contained" color="primary" sx={{ fontWeight: 700 }}>
            Next
          </Button>
        ) : (
          <Button
            onClick={handleRunEstimation}
            variant="contained"
            color="primary"
            disabled={analyzing}
            startIcon={analyzing ? <CircularProgress size={16} color="inherit" /> : <CheckCircleIcon />}
            sx={{ fontWeight: 700 }}
          >
            {analyzing ? 'Evaluating & Saving...' : 'Run & Save Estimate'}
          </Button>
        )}
      </DialogActions>
    </Dialog>
  );
};
