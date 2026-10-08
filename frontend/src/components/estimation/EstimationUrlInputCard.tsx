import React from 'react';
import {
  Box,
  Typography,
  Stack,
  Card,
  CardContent,
  Grid,
  TextField,
  Button,
  Chip,
  Tabs,
  Tab,
  InputAdornment,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Checkbox,
  CircularProgress,
  useTheme,
} from '@mui/material';
import { alpha } from '@mui/material/styles';
import TravelExploreIcon from '@mui/icons-material/TravelExplore';
import LinkIcon from '@mui/icons-material/Link';
import LanguageIcon from '@mui/icons-material/Language';
import SearchIcon from '@mui/icons-material/Search';
import PlaylistAddCheckIcon from '@mui/icons-material/PlaylistAddCheck';
import CalculateIcon from '@mui/icons-material/Calculate';
import ArrowForwardIcon from '@mui/icons-material/ArrowForward';
import type { DiscoveredUrlItem } from '../../service/estimationService';

interface EstimationUrlInputCardProps {
  inputMode: number;
  onInputModeChange: (mode: number) => void;
  baseUrl: string;
  onBaseUrlChange: (url: string) => void;
  discoveryDepth: number;
  onDiscoveryDepthChange: (depth: number) => void;
  maxDiscovery: number;
  onMaxDiscoveryChange: (max: number) => void;
  discovering: boolean;
  onDiscover: (e?: React.FormEvent) => void;
  discoveredPages: DiscoveredUrlItem[];
  selectedUrls: Record<string, boolean>;
  onToggleUrl: (url: string) => void;
  onSelectAll: () => void;
  onDeselectAll: () => void;
  filterKeyword: string;
  onFilterKeywordChange: (keyword: string) => void;
  customUrlsText: string;
  onCustomUrlsTextChange: (text: string) => void;
  analyzing: boolean;
  onAnalyzeSelected: () => void;
}

export const EstimationUrlInputCard: React.FC<EstimationUrlInputCardProps> = ({
  inputMode,
  onInputModeChange,
  baseUrl,
  onBaseUrlChange,
  discoveryDepth,
  onDiscoveryDepthChange,
  maxDiscovery,
  onMaxDiscoveryChange,
  discovering,
  onDiscover,
  discoveredPages,
  selectedUrls,
  onToggleUrl,
  onSelectAll,
  onDeselectAll,
  filterKeyword,
  onFilterKeywordChange,
  customUrlsText,
  onCustomUrlsTextChange,
  analyzing,
  onAnalyzeSelected,
}) => {
  const theme = useTheme();

  const selectedCount = Object.values(selectedUrls).filter(Boolean).length;
  const parsedCustomUrls = customUrlsText
    .split(/[\n,]+/)
    .map((u) => u.trim())
    .filter((u) => u.length > 0);

  const filteredDiscoveredPages = discoveredPages.filter((item) => {
    if (!filterKeyword) return true;
    const k = filterKeyword.toLowerCase();
    return item.path.toLowerCase().includes(k) || item.url.toLowerCase().includes(k);
  });

  return (
    <Card
      sx={{
        mb: 4,
        borderRadius: 4,
        border: '1px solid',
        borderColor: theme.palette.divider,
        boxShadow: `0 4px 20px -2px ${alpha(theme.palette.text.primary, 0.05)}`,
        bgcolor: theme.palette.background.paper,
        overflow: 'hidden',
      }}
    >
      <Box
        sx={{
          borderBottom: 1,
          borderColor: theme.palette.divider,
          bgcolor: alpha(theme.palette.background.default, 0.8),
          px: 2,
          pt: 1,
        }}
      >
        <Tabs
          value={inputMode}
          onChange={(_, val) => onInputModeChange(val)}
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
            sx={{ fontWeight: 700, textTransform: 'none', py: 1.8, fontSize: '0.925rem' }}
          />
          <Tab
            icon={<LinkIcon sx={{ fontSize: 19 }} />}
            iconPosition="start"
            label="Mode B: Direct URL List (Client-Provided URLs)"
            sx={{ fontWeight: 700, textTransform: 'none', py: 1.8, fontSize: '0.925rem' }}
          />
        </Tabs>
      </Box>

      <CardContent sx={{ p: { xs: 2.5, md: 3.5 } }}>
        {/* Quick Sample Presets */}
        <Stack
          component="div"
          direction="row"
          spacing={1}
          sx={{ alignItems: 'center', mb: 2.5, flexWrap: 'wrap', gap: 1 }}
        >
          <Typography variant="caption" sx={{ fontWeight: 700, color: 'text.secondary', mr: 0.5 }}>
            QUICK SAMPLE PRESETS:
          </Typography>
          <Chip
            label="WinVinaya.com (Corporate Static)"
            size="small"
            clickable
            onClick={() => {
              if (inputMode === 0) {
                onBaseUrlChange('https://winvinaya.com');
              } else {
                onCustomUrlsTextChange(
                  'https://winvinaya.com\nhttps://winvinaya.com/about-us/\nhttps://winvinaya.com/contact-us/'
                );
              }
            }}
            sx={{
              fontWeight: 600,
              bgcolor: alpha(theme.palette.info.main, 0.08),
              color: theme.palette.info.main,
              border: `1px solid ${alpha(theme.palette.info.main, 0.25)}`,
              '&:hover': { bgcolor: alpha(theme.palette.info.main, 0.16) },
            }}
          />
          <Chip
            label="Lemonn.co.in (FinTech Portal)"
            size="small"
            clickable
            onClick={() => {
              if (inputMode === 0) {
                onBaseUrlChange('https://lemonn.co.in');
              } else {
                onCustomUrlsTextChange(
                  'https://lemonn.co.in/\nhttps://lemonn.co.in/ipo\nhttps://lemonn.co.in/mutual-funds'
                );
              }
            }}
            sx={{
              fontWeight: 600,
              bgcolor: alpha(theme.palette.success.main, 0.08),
              color: theme.palette.success.main,
              border: `1px solid ${alpha(theme.palette.success.main, 0.25)}`,
              '&:hover': { bgcolor: alpha(theme.palette.success.main, 0.16) },
            }}
          />
        </Stack>

        {/* Mode 0: Crawl & Discover from Base URL */}
        {inputMode === 0 && (
          <Box>
            <form onSubmit={onDiscover}>
              <Grid container spacing={2.5} component="div" sx={{ alignItems: 'flex-start' }}>
                <Grid size={{ xs: 12, md: 6 }} component="div">
                  <Typography
                    variant="caption"
                    sx={{ fontWeight: 700, color: 'text.secondary', display: 'block', mb: 0.75 }}
                  >
                    TARGET ROOT DOMAIN / BASE URL
                  </Typography>
                  <TextField
                    fullWidth
                    placeholder="https://winvinaya.com"
                    value={baseUrl}
                    onChange={(e) => onBaseUrlChange(e.target.value)}
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
                  <Typography
                    variant="caption"
                    sx={{ fontWeight: 700, color: 'text.secondary', display: 'block', mb: 0.75 }}
                  >
                    CRAWL DEPTH
                  </Typography>
                  <TextField
                    fullWidth
                    select
                    value={discoveryDepth}
                    onChange={(e) => onDiscoveryDepthChange(Number(e.target.value))}
                    slotProps={{ select: { native: true } }}
                  >
                    <option value={1}>Level 1 (Direct Links)</option>
                    <option value={2}>Level 2 (Internal Sub-pages)</option>
                    <option value={3}>Level 3 (Deep Discovery)</option>
                  </TextField>
                </Grid>

                <Grid size={{ xs: 6, md: 2 }} component="div">
                  <Typography
                    variant="caption"
                    sx={{ fontWeight: 700, color: 'text.secondary', display: 'block', mb: 0.75 }}
                  >
                    MAX DISCOVERY
                  </Typography>
                  <TextField
                    fullWidth
                    type="number"
                    value={maxDiscovery}
                    onChange={(e) => onMaxDiscoveryChange(Math.max(5, Number(e.target.value)))}
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
                      fontWeight: 700,
                      borderRadius: 2,
                      textTransform: 'none',
                      boxShadow: `0 4px 14px ${alpha(theme.palette.primary.main, 0.25)}`,
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
                  bgcolor: alpha(theme.palette.background.default, 0.85),
                  borderRadius: 3,
                  border: '1px solid',
                  borderColor: theme.palette.divider,
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
                      <Typography variant="subtitle1" sx={{ fontWeight: 800 }}>
                        Discovered Pages ({discoveredPages.length})
                      </Typography>
                      <Chip
                        label={`${selectedCount} Selected`}
                        size="small"
                        color={selectedCount > 0 ? 'primary' : 'default'}
                        sx={{ fontWeight: 800 }}
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
                      onChange={(e) => onFilterKeywordChange(e.target.value)}
                      slotProps={{
                        input: {
                          startAdornment: (
                            <InputAdornment position="start">
                              <SearchIcon fontSize="small" color="action" />
                            </InputAdornment>
                          ),
                        },
                      }}
                      sx={{ width: { xs: '100%', sm: 220 }, bgcolor: theme.palette.background.paper }}
                    />
                    <Button
                      size="small"
                      variant="outlined"
                      onClick={onSelectAll}
                      sx={{ fontWeight: 700, textTransform: 'none' }}
                    >
                      Select All
                    </Button>
                    <Button
                      size="small"
                      variant="outlined"
                      color="inherit"
                      onClick={onDeselectAll}
                      sx={{ fontWeight: 700, textTransform: 'none' }}
                    >
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
                    borderColor: theme.palette.divider,
                    borderRadius: 2,
                    mb: 2.5,
                    boxShadow: 'none',
                  }}
                >
                  <Table size="small" stickyHeader>
                    <TableHead>
                      <TableRow>
                        <TableCell padding="checkbox" sx={{ bgcolor: theme.palette.grey[100], width: 48 }}>
                          <Checkbox
                            indeterminate={selectedCount > 0 && selectedCount < discoveredPages.length}
                            checked={discoveredPages.length > 0 && selectedCount === discoveredPages.length}
                            onChange={(e) => (e.target.checked ? onSelectAll() : onDeselectAll())}
                          />
                        </TableCell>
                        <TableCell sx={{ bgcolor: theme.palette.grey[100], fontWeight: 800, width: 220 }}>
                          Route Path
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
                            onClick={() => onToggleUrl(item.url)}
                            sx={{
                              cursor: 'pointer',
                              bgcolor: isChecked ? alpha(theme.palette.primary.main, 0.05) : undefined,
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
                                  fontWeight: 700,
                                  color: isChecked ? theme.palette.primary.main : theme.palette.text.secondary,
                                  borderColor: isChecked ? theme.palette.primary.main : theme.palette.divider,
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
                    onClick={onAnalyzeSelected}
                    disabled={analyzing || selectedCount === 0}
                    startIcon={analyzing ? <CircularProgress size={18} color="inherit" /> : <CalculateIcon />}
                    endIcon={<ArrowForwardIcon />}
                    sx={{
                      fontWeight: 800,
                      px: 4,
                      py: 1.5,
                      borderRadius: 2,
                      textTransform: 'none',
                      boxShadow: `0 4px 16px ${alpha(theme.palette.primary.main, 0.3)}`,
                    }}
                  >
                    {analyzing
                      ? 'Analyzing Page Complexity...'
                      : `Calculate Estimation for (${selectedCount}) Pages`}
                  </Button>
                </Stack>
              </Box>
            )}
          </Box>
        )}

        {/* Mode 1: Direct Custom URL List */}
        {inputMode === 1 && (
          <Box>
            <Typography
              variant="caption"
              sx={{ fontWeight: 700, color: 'text.secondary', display: 'block', mb: 1 }}
            >
              PASTE CLIENT-SPECIFIED URLS (ONE PER LINE OR COMMA-SEPARATED)
            </Typography>
            <TextField
              fullWidth
              multiline
              rows={6}
              placeholder={`https://winvinaya.com\nhttps://winvinaya.com/about-us/\nhttps://winvinaya.com/contact-us/`}
              value={customUrlsText}
              onChange={(e) => onCustomUrlsTextChange(e.target.value)}
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
                sx={{ fontWeight: 700, py: 0.5 }}
              />

              <Button
                variant="contained"
                color="primary"
                size="large"
                onClick={onAnalyzeSelected}
                disabled={analyzing || parsedCustomUrls.length === 0}
                startIcon={analyzing ? <CircularProgress size={18} color="inherit" /> : <CalculateIcon />}
                endIcon={<ArrowForwardIcon />}
                sx={{
                  fontWeight: 800,
                  px: 4,
                  py: 1.5,
                  borderRadius: 2,
                  textTransform: 'none',
                  boxShadow: `0 4px 16px ${alpha(theme.palette.primary.main, 0.3)}`,
                }}
              >
                {analyzing
                  ? 'Analyzing Page Complexity...'
                  : `Calculate Estimation for (${parsedCustomUrls.length}) Pages`}
              </Button>
            </Stack>
          </Box>
        )}
      </CardContent>
    </Card>
  );
};
