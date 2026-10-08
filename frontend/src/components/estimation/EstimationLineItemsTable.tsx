import React from 'react';
import {
  Box,
  Typography,
  Stack,
  Card,
  Grid,
  Button,
  Chip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableFooter,
  TableRow,
  Select,
  MenuItem,
  IconButton,
  Collapse,
  Tooltip,
  CircularProgress,
  useTheme,
} from '@mui/material';
import { alpha } from '@mui/material/styles';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import OpenInNewIcon from '@mui/icons-material/OpenInNew';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import FileDownloadIcon from '@mui/icons-material/FileDownload';
import DescriptionIcon from '@mui/icons-material/Description';
import type { EstimationResult, EstimatedPage } from '../../service/estimationService';

interface EstimationLineItemsTableProps {
  result: EstimationResult;
  expandedRows: Record<number, boolean>;
  onToggleRow: (index: number) => void;
  onComplexityOverride: (pageIndex: number, newComplexity: 'simple' | 'medium' | 'complex') => void;
  exportingExcel: boolean;
  exportingPdf: boolean;
  onDownloadExcel: () => void;
  onDownloadPdf: () => void;
}

export const EstimationLineItemsTable: React.FC<EstimationLineItemsTableProps> = ({
  result,
  expandedRows,
  onToggleRow,
  onComplexityOverride,
  exportingExcel,
  exportingPdf,
  onDownloadExcel,
  onDownloadPdf,
}) => {
  const theme = useTheme();

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

  return (
    <Card
      sx={{
        borderRadius: 4,
        border: '1px solid',
        borderColor: theme.palette.divider,
        boxShadow: `0 4px 20px -2px ${alpha(theme.palette.text.primary, 0.05)}`,
        bgcolor: theme.palette.background.paper,
        overflow: 'hidden',
      }}
    >
      {/* Table Header Action Bar */}
      <Box
        sx={{
          p: 3,
          borderBottom: '1px solid',
          borderColor: theme.palette.divider,
          bgcolor: alpha(theme.palette.background.default, 0.6),
        }}
      >
        <Stack
          component="div"
          direction={{ xs: 'column', sm: 'row' }}
          spacing={2}
          sx={{ justifyContent: 'space-between', alignItems: { xs: 'flex-start', sm: 'center' } }}
        >
          <Box>
            <Typography variant="h6" sx={{ fontWeight: 800, color: theme.palette.text.primary }}>
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
              onClick={onDownloadExcel}
              disabled={exportingExcel}
              sx={{
                bgcolor: theme.palette.success.main,
                color: '#ffffff',
                fontWeight: 700,
                borderRadius: 2,
                textTransform: 'none',
                '&:hover': { bgcolor: theme.palette.success.dark },
              }}
            >
              Export Excel
            </Button>
            <Button
              size="small"
              variant="contained"
              startIcon={exportingPdf ? <CircularProgress size={14} color="inherit" /> : <DescriptionIcon />}
              onClick={onDownloadPdf}
              disabled={exportingPdf}
              sx={{
                bgcolor: theme.palette.info.main,
                color: '#ffffff',
                fontWeight: 700,
                borderRadius: 2,
                textTransform: 'none',
                '&:hover': { bgcolor: theme.palette.info.dark },
              }}
            >
              Export PDF
            </Button>
          </Stack>
        </Stack>
      </Box>

      <TableContainer>
        <Table>
          <TableHead sx={{ bgcolor: alpha(theme.palette.background.default, 0.7) }}>
            <TableRow>
              <TableCell sx={{ fontWeight: 800, width: 48 }}>#</TableCell>
              <TableCell sx={{ fontWeight: 800 }}>Page Title & Target URL</TableCell>
              <TableCell sx={{ fontWeight: 800 }}>Complexity Tier</TableCell>
              <TableCell align="center" sx={{ fontWeight: 800 }}>Manual Effort</TableCell>
              <TableCell align="center" sx={{ fontWeight: 800 }}>Manual Cost</TableCell>
              <TableCell align="center" sx={{ fontWeight: 800 }}>API Cost</TableCell>
              <TableCell align="center" sx={{ fontWeight: 800 }}>Platform Fee</TableCell>
              <TableCell align="right" sx={{ fontWeight: 800 }}>Base Cost (A)</TableCell>
              <TableCell align="right" sx={{ fontWeight: 800 }}>Margin ({result.summary.profit_margin_pct}%) (B)</TableCell>
              <TableCell align="right" sx={{ fontWeight: 800, color: theme.palette.primary.main }}>Total Cost (A+B)</TableCell>
              <TableCell align="center" sx={{ fontWeight: 800 }}>Evidence</TableCell>
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
                      bgcolor: isExpanded ? alpha(theme.palette.background.default, 0.8) : undefined,
                    }}
                  >
                    <TableCell sx={{ fontWeight: 700, color: 'text.secondary' }}>{idx + 1}</TableCell>
                    <TableCell sx={{ maxWidth: '320px' }}>
                      <Typography variant="subtitle2" noWrap sx={{ fontWeight: 700 }}>
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
                          onComplexityOverride(
                            idx,
                            e.target.value as 'simple' | 'medium' | 'complex'
                          )
                        }
                        sx={{
                          fontSize: '0.8rem',
                          fontWeight: 800,
                          borderRadius: 2,
                          '& .MuiSelect-select': { py: 0.6, px: 1 },
                        }}
                      >
                        <MenuItem value="simple" sx={{ fontWeight: 700, color: theme.palette.success.dark }}>
                          Simple (1.0 hr)
                        </MenuItem>
                        <MenuItem value="medium" sx={{ fontWeight: 700, color: theme.palette.warning.dark }}>
                          Medium (2.5 hrs)
                        </MenuItem>
                        <MenuItem value="complex" sx={{ fontWeight: 700, color: theme.palette.error.dark }}>
                          Complex (5.5 hrs)
                        </MenuItem>
                      </Select>
                    </TableCell>
                    <TableCell align="center">
                      <Typography variant="body2" sx={{ fontWeight: 700 }}>
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
                      <Typography variant="body2" sx={{ color: theme.palette.success.dark, fontWeight: 600 }}>
                        ${p.base_cost.toFixed(2)}
                      </Typography>
                    </TableCell>
                    <TableCell align="right">
                      <Typography variant="body2" sx={{ color: theme.palette.success.dark, fontWeight: 600 }}>
                        ${p.profit_margin.toFixed(2)}
                      </Typography>
                    </TableCell>
                    <TableCell align="right">
                      <Typography variant="subtitle2" sx={{ fontWeight: 800, color: theme.palette.primary.main, fontSize: '0.95rem' }}>
                        ${p.final_cost.toFixed(2)}
                      </Typography>
                    </TableCell>
                    <TableCell align="center">
                      <IconButton
                        size="small"
                        onClick={() => onToggleRow(idx)}
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
                        <Box
                          sx={{
                            p: 3,
                            bgcolor: alpha(theme.palette.background.default, 0.8),
                            borderRadius: 3,
                            my: 1.5,
                            border: '1px solid',
                            borderColor: theme.palette.divider,
                          }}
                        >
                          <Grid container spacing={3} component="div">
                            {/* Left: Identified Triggers */}
                            <Grid size={{ xs: 12, md: 7 }} component="div">
                              <Typography variant="subtitle2" sx={{ fontWeight: 800, mb: 1 }}>
                                Detection Evidence & Complexity Triggers:
                              </Typography>
                              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                                {p.summary_rationale}
                              </Typography>

                              <Typography variant="caption" sx={{ fontWeight: 800, display: 'block', mb: 1, color: 'text.secondary' }}>
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
                                    sx={{ fontWeight: 600 }}
                                  />
                                ))}
                              </Box>
                            </Grid>

                            {/* Right: DOM Element Inventory Breakdown */}
                            <Grid size={{ xs: 12, md: 5 }} component="div">
                              <Typography variant="subtitle2" sx={{ fontWeight: 800, mb: 1 }}>
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
                                    <Box
                                      sx={{
                                        p: 1,
                                        bgcolor: theme.palette.background.paper,
                                        borderRadius: 1.5,
                                        border: `1px solid ${theme.palette.divider}`,
                                      }}
                                    >
                                      <Typography variant="caption" color="text.secondary" sx={{ display: 'block' }}>
                                        {stat.label}
                                      </Typography>
                                      <Typography variant="subtitle2" sx={{ fontWeight: 800 }}>
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

          {/* Table Footer: Logical Page-Wise Column Totals */}
          <TableFooter sx={{ bgcolor: theme.palette.grey[100], borderTop: '2px solid', borderColor: theme.palette.divider }}>
            <TableRow>
              <TableCell sx={{ fontWeight: 800, color: theme.palette.primary.main }}>Σ</TableCell>
              <TableCell sx={{ fontWeight: 800, color: theme.palette.primary.main }}>
                TOTAL ({result.summary.total_pages} Pages)
              </TableCell>
              <TableCell>
                <Typography variant="caption" sx={{ fontWeight: 700, color: 'text.secondary' }}>
                  {result.summary.simple_pages} Simple · {result.summary.medium_pages} Medium · {result.summary.complex_pages} Complex
                </Typography>
              </TableCell>
              <TableCell align="center" sx={{ fontWeight: 800 }}>
                {result.summary.total_manual_hours.toFixed(1)} hrs
              </TableCell>
              <TableCell align="center" sx={{ fontWeight: 800 }}>
                ${result.summary.total_manual_cost.toFixed(2)}
              </TableCell>
              <TableCell align="center" sx={{ fontWeight: 800 }}>
                ${result.summary.total_api_cost.toFixed(2)}
              </TableCell>
              <TableCell align="center" sx={{ fontWeight: 800 }}>
                ${result.summary.total_platform_cost.toFixed(2)}
              </TableCell>
              <TableCell align="right" sx={{ fontWeight: 800, color: theme.palette.success.dark }}>
                ${result.summary.total_base_cost.toFixed(2)}
              </TableCell>
              <TableCell align="right" sx={{ fontWeight: 800, color: theme.palette.success.dark }}>
                ${result.summary.total_profit_margin.toFixed(2)}
              </TableCell>
              <TableCell align="right" sx={{ fontWeight: 800, color: theme.palette.primary.main, fontSize: '1.05rem' }}>
                ${result.summary.total_final_cost.toFixed(2)}
              </TableCell>
              <TableCell />
            </TableRow>
          </TableFooter>
        </Table>
      </TableContainer>
    </Card>
  );
};
