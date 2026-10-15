import React, { useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Box,
  Typography,
  Stack,
  Chip,
  Tabs,
  Tab,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  LinearProgress,
  IconButton,
  useTheme
} from '@mui/material';
import CloseIcon from '@mui/icons-material/Close';
import SmartToyIcon from '@mui/icons-material/SmartToy';
import MonetizationOnIcon from '@mui/icons-material/MonetizationOn';
import MemoryIcon from '@mui/icons-material/Memory';
import BugReportIcon from '@mui/icons-material/BugReport';
import AssignmentTurnedInIcon from '@mui/icons-material/AssignmentTurnedIn';
import InfoOutlinedIcon from '@mui/icons-material/InfoOutlined';
import LayersIcon from '@mui/icons-material/Layers';
import TableChartIcon from '@mui/icons-material/TableChart';
import type { TokenUsage } from '../../../service/auditService';

interface Props {
  open: boolean;
  onClose: () => void;
  tokenUsage?: TokenUsage | null;
}

export const LLMCostBreakdownModal: React.FC<Props> = ({ open, onClose, tokenUsage }) => {
  const theme = useTheme();
  const [activeTab, setActiveTab] = useState<'operation' | 'provider' | 'pricing'>('operation');

  const costTotal = tokenUsage?.cost_usd_total ?? tokenUsage?.totals?.cost_usd ?? tokenUsage?.cost_estimate_usd ?? 0.0;
  const tokensTotal = tokenUsage?.tokens_total ?? tokenUsage?.totals?.total_tokens ?? 0;
  const callsTotal = tokenUsage?.llm_calls ?? tokenUsage?.totals?.calls ?? 0;
  const inputTotal = tokenUsage?.totals?.input_tokens ?? tokenUsage?.tokens_sent ?? 0;
  const outputTotal = tokenUsage?.totals?.output_tokens ?? tokenUsage?.tokens_received ?? 0;

  const byProvider = tokenUsage?.cost_by_provider || {};
  const byCategory = tokenUsage?.cost_by_category || {};

  const categoriesList = [
    {
      key: 'defect',
      label: byCategory['defect']?.label || 'Defect Remediation & Analysis',
      subtitle: 'Root cause analysis, severity assessment & code remediation suggestions',
      icon: <BugReportIcon fontSize="small" sx={{ color: theme.palette.error.main }} />,
      color: theme.palette.error.main,
      data: byCategory['defect'] || { calls: 0, input_tokens: 0, output_tokens: 0, total_tokens: 0, cost_usd: 0 }
    },
    {
      key: 'testcase',
      label: byCategory['testcase']?.label || 'Test Case Synthesis & Evaluation',
      subtitle: 'Multi-agent test case synthesis, acceptance criteria & WCAG verification',
      icon: <AssignmentTurnedInIcon fontSize="small" sx={{ color: theme.palette.primary.main }} />,
      color: theme.palette.primary.main,
      data: byCategory['testcase'] || { calls: 0, input_tokens: 0, output_tokens: 0, total_tokens: 0, cost_usd: 0 }
    },
    {
      key: 'other',
      label: byCategory['other']?.label || 'Other Operations (Planning, Summary, Vision)',
      subtitle: 'Audit strategy, manager agent reasoning, executive summary & screenshot analysis',
      icon: <InfoOutlinedIcon fontSize="small" sx={{ color: theme.palette.warning.main }} />,
      color: theme.palette.warning.main,
      data: byCategory['other'] || { calls: 0, input_tokens: 0, output_tokens: 0, total_tokens: 0, cost_usd: 0 }
    }
  ];

  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="lg"
      fullWidth
    >
      {/* Modal Header */}
      <DialogTitle
        sx={{
          p: 0,
          background: 'linear-gradient(135deg, #0f172a 0%, #1e293b 100%)',
          color: '#ffffff'
        }}
      >
        <Box
          sx={{
            p: 3,
            display: 'flex',
            flexWrap: 'wrap',
            alignItems: 'center',
            justifyContent: 'space-between',
            gap: 2
          }}
        >
          <Stack component="div" direction="row" spacing={1.5} sx={{ alignItems: 'center' }}>
            <Box
              sx={{
                p: 1.2,
                borderRadius: '12px',
                bgcolor: 'rgba(56, 189, 248, 0.15)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}
            >
              <SmartToyIcon sx={{ color: '#38bdf8', fontSize: 28 }} />
            </Box>
            <Box>
              <Typography variant="h6" sx={{ fontWeight: '800', lineHeight: 1.2 }}>
                AI & LLM Cost Breakdown
              </Typography>
              <Typography variant="caption" sx={{ color: '#94a3b8' }}>
                Real-time token consumption and USD expense for this accessibility audit run
              </Typography>
            </Box>
          </Stack>

          <Stack component="div" direction="row" spacing={1.5} sx={{ alignItems: 'center' }}>
            <Chip
              icon={<MonetizationOnIcon sx={{ color: '#4ade80 !important' }} />}
              label={`Total Cost: $${costTotal.toFixed(4)}`}
              sx={{
                bgcolor: 'rgba(74, 222, 128, 0.15)',
                color: '#4ade80',
                fontWeight: '800',
                fontSize: '0.85rem',
                border: '1px solid rgba(74, 222, 128, 0.3)',
                py: 0.5
              }}
            />
            <Chip
              icon={<MemoryIcon sx={{ color: '#38bdf8 !important' }} />}
              label={`${tokensTotal.toLocaleString()} Tokens`}
              sx={{
                bgcolor: 'rgba(56, 189, 248, 0.15)',
                color: '#38bdf8',
                fontWeight: '700',
                border: '1px solid rgba(56, 189, 248, 0.3)'
              }}
            />
            <IconButton onClick={onClose} sx={{ color: '#94a3b8', '&:hover': { color: '#ffffff' } }}>
              <CloseIcon />
            </IconButton>
          </Stack>
        </Box>

        {/* Navigation Tabs */}
        <Box sx={{ px: 3, borderTop: '1px solid rgba(255,255,255,0.08)' }}>
          <Tabs
            value={activeTab}
            onChange={(_, val) => setActiveTab(val)}
            textColor="inherit"
            indicatorColor="primary"
            sx={{
              minHeight: '44px',
              '& .MuiTabs-indicator': { bgcolor: '#38bdf8', height: 3 },
              '& .MuiTab-root': {
                color: '#94a3b8',
                fontWeight: '700',
                textTransform: 'none',
                minHeight: '44px',
                '&.Mui-selected': { color: '#38bdf8' }
              }
            }}
          >
            <Tab
              value="operation"
              label="Cost by Operation (Defects / Test Cases / Other)"
              icon={<LayersIcon fontSize="small" />}
              iconPosition="start"
            />
            <Tab
              value="provider"
              label="Cost by AI Provider (Claude Sonnet / Gemini)"
              icon={<SmartToyIcon fontSize="small" />}
              iconPosition="start"
            />
            <Tab
              value="pricing"
              label="Model Pricing & Rate Card"
              icon={<TableChartIcon fontSize="small" />}
              iconPosition="start"
            />
          </Tabs>
        </Box>
      </DialogTitle>

      {/* Modal Content */}
      <DialogContent sx={{ p: 3, pt: 3.5 }}>
        {/* Tab 1: By Operation */}
        {activeTab === 'operation' && (
          <Box>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              Exact token consumption and dollar expenditure broken down by functional audit task:
            </Typography>

            <TableContainer component={Paper} variant="outlined" sx={{ borderRadius: '12px', overflow: 'hidden' }}>
              <Table size="small">
                <TableHead sx={{ bgcolor: 'action.hover' }}>
                  <TableRow>
                    <TableCell sx={{ fontWeight: '700' }}>Audit Operation</TableCell>
                    <TableCell align="center" sx={{ fontWeight: '700' }}>API Calls</TableCell>
                    <TableCell align="center" sx={{ fontWeight: '700' }}>Input Tokens</TableCell>
                    <TableCell align="center" sx={{ fontWeight: '700' }}>Output Tokens</TableCell>
                    <TableCell align="center" sx={{ fontWeight: '700' }}>Total Tokens</TableCell>
                    <TableCell align="right" sx={{ fontWeight: '700' }}>Cost (USD)</TableCell>
                    <TableCell align="left" sx={{ fontWeight: '700', width: '160px' }}>Cost Share</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {categoriesList.map((cat) => {
                    const cData = cat.data;
                    const cCost = cData.cost_usd || 0;
                    const sharePct = costTotal > 0 ? (cCost / costTotal) * 100 : 0;

                    return (
                      <TableRow key={cat.key} hover>
                        <TableCell>
                          <Stack component="div" direction="row" spacing={1.5} sx={{ alignItems: 'center' }}>
                            {cat.icon}
                            <Box>
                              <Typography variant="body2" sx={{ fontWeight: '700' }}>
                                {cat.label}
                              </Typography>
                              <Typography variant="caption" color="text.secondary">
                                {cat.subtitle}
                              </Typography>
                            </Box>
                          </Stack>
                        </TableCell>
                        <TableCell align="center">
                          <Chip label={cData.calls || 0} size="small" variant="outlined" />
                        </TableCell>
                        <TableCell align="center">
                          <Typography variant="body2" sx={{ fontFamily: 'monospace' }}>
                            {(cData.input_tokens || 0).toLocaleString()}
                          </Typography>
                        </TableCell>
                        <TableCell align="center">
                          <Typography variant="body2" sx={{ fontFamily: 'monospace' }}>
                            {(cData.output_tokens || 0).toLocaleString()}
                          </Typography>
                        </TableCell>
                        <TableCell align="center">
                          <Typography variant="body2" sx={{ fontFamily: 'monospace', fontWeight: '700' }}>
                            {(cData.total_tokens || 0).toLocaleString()}
                          </Typography>
                        </TableCell>
                        <TableCell align="right">
                          <Typography
                            variant="body2"
                            sx={{
                              fontWeight: '700',
                              color: cCost > 0 ? 'text.primary' : 'text.secondary'
                            }}
                          >
                            ${cCost.toFixed(4)}
                          </Typography>
                        </TableCell>
                        <TableCell align="left">
                          <Stack component="div" direction="row" spacing={1} sx={{ alignItems: 'center' }}>
                            <Box sx={{ width: '90px' }}>
                              <LinearProgress
                                variant="determinate"
                                value={sharePct}
                                sx={{
                                  height: 6,
                                  borderRadius: 3,
                                  bgcolor: '#e2e8f0',
                                  '& .MuiLinearProgress-bar': { bgcolor: cat.color, borderRadius: 3 }
                                }}
                              />
                            </Box>
                            <Typography variant="caption" sx={{ fontWeight: '700', color: 'text.secondary' }}>
                              {sharePct.toFixed(1)}%
                            </Typography>
                          </Stack>
                        </TableCell>
                      </TableRow>
                    );
                  })}
                  <TableRow sx={{ bgcolor: 'action.selected' }}>
                    <TableCell sx={{ fontWeight: '800' }}>Total (All Operations)</TableCell>
                    <TableCell align="center" sx={{ fontWeight: '800' }}>{callsTotal}</TableCell>
                    <TableCell align="center" sx={{ fontFamily: 'monospace', fontWeight: '800' }}>
                      {inputTotal.toLocaleString()}
                    </TableCell>
                    <TableCell align="center" sx={{ fontFamily: 'monospace', fontWeight: '800' }}>
                      {outputTotal.toLocaleString()}
                    </TableCell>
                    <TableCell align="center" sx={{ fontFamily: 'monospace', fontWeight: '800' }}>
                      {tokensTotal.toLocaleString()}
                    </TableCell>
                    <TableCell align="right" sx={{ fontWeight: '800', color: 'success.dark', fontSize: '0.95rem' }}>
                      ${costTotal.toFixed(4)}
                    </TableCell>
                    <TableCell align="left">
                      <Typography variant="caption" sx={{ fontWeight: '800' }}>100%</Typography>
                    </TableCell>
                  </TableRow>
                </TableBody>
              </Table>
            </TableContainer>
          </Box>
        )}

        {/* Tab 2: By Provider */}
        {activeTab === 'provider' && (
          <Box>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              Separate consumption for Claude Sonnet vs Gemini recorded during the audit run:
            </Typography>

            <TableContainer component={Paper} variant="outlined" sx={{ borderRadius: '12px', overflow: 'hidden' }}>
              <Table size="small">
                <TableHead sx={{ bgcolor: 'action.hover' }}>
                  <TableRow>
                    <TableCell sx={{ fontWeight: '700' }}>AI Provider & Model</TableCell>
                    <TableCell align="center" sx={{ fontWeight: '700' }}>API Calls</TableCell>
                    <TableCell align="center" sx={{ fontWeight: '700' }}>Input Tokens</TableCell>
                    <TableCell align="center" sx={{ fontWeight: '700' }}>Output Tokens</TableCell>
                    <TableCell align="center" sx={{ fontWeight: '700' }}>Total Tokens</TableCell>
                    <TableCell align="right" sx={{ fontWeight: '700' }}>Cost (USD)</TableCell>
                    <TableCell align="left" sx={{ fontWeight: '700', width: '160px' }}>Cost Share</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {Object.entries(byProvider).map(([pKey, pData]) => {
                    const label = pData.label || pKey.toUpperCase();
                    const pCost = pData.cost_usd || 0;
                    const sharePct = costTotal > 0 ? (pCost / costTotal) * 100 : 0;
                    const isClaude = pKey.toLowerCase().includes('claude');
                    const color = isClaude ? '#f97316' : '#3b82f6';

                    return (
                      <TableRow key={pKey} hover>
                        <TableCell>
                          <Stack component="div" direction="row" spacing={1.5} sx={{ alignItems: 'center' }}>
                            <Box
                              sx={{
                                width: 12,
                                height: 12,
                                borderRadius: '50%',
                                bgcolor: color
                              }}
                            />
                            <Box>
                              <Typography variant="body2" sx={{ fontWeight: '700' }}>
                                {label}
                              </Typography>
                              <Typography variant="caption" color="text.secondary">
                                {isClaude ? 'Anthropic claude-sonnet-4-6' : 'Google gemini-3.5-flash'}
                              </Typography>
                            </Box>
                          </Stack>
                        </TableCell>
                        <TableCell align="center">
                          <Chip label={pData.calls || 0} size="small" variant="outlined" />
                        </TableCell>
                        <TableCell align="center">
                          <Typography variant="body2" sx={{ fontFamily: 'monospace' }}>
                            {(pData.input_tokens || 0).toLocaleString()}
                          </Typography>
                        </TableCell>
                        <TableCell align="center">
                          <Typography variant="body2" sx={{ fontFamily: 'monospace' }}>
                            {(pData.output_tokens || 0).toLocaleString()}
                          </Typography>
                        </TableCell>
                        <TableCell align="center">
                          <Typography variant="body2" sx={{ fontFamily: 'monospace', fontWeight: '700' }}>
                            {(pData.total_tokens || 0).toLocaleString()}
                          </Typography>
                        </TableCell>
                        <TableCell align="right">
                          <Typography variant="body2" sx={{ fontWeight: '700' }}>
                            ${pCost.toFixed(4)}
                          </Typography>
                        </TableCell>
                        <TableCell align="left">
                          <Stack component="div" direction="row" spacing={1} sx={{ alignItems: 'center' }}>
                            <Box sx={{ width: '90px' }}>
                              <LinearProgress
                                variant="determinate"
                                value={sharePct}
                                sx={{
                                  height: 6,
                                  borderRadius: 3,
                                  bgcolor: '#e2e8f0',
                                  '& .MuiLinearProgress-bar': { bgcolor: color, borderRadius: 3 }
                                }}
                              />
                            </Box>
                            <Typography variant="caption" sx={{ fontWeight: '700', color: 'text.secondary' }}>
                              {sharePct.toFixed(1)}%
                            </Typography>
                          </Stack>
                        </TableCell>
                      </TableRow>
                    );
                  })}
                  <TableRow sx={{ bgcolor: 'action.selected' }}>
                    <TableCell sx={{ fontWeight: '800' }}>Total (All Models)</TableCell>
                    <TableCell align="center" sx={{ fontWeight: '800' }}>{callsTotal}</TableCell>
                    <TableCell align="center" sx={{ fontFamily: 'monospace', fontWeight: '800' }}>
                      {inputTotal.toLocaleString()}
                    </TableCell>
                    <TableCell align="center" sx={{ fontFamily: 'monospace', fontWeight: '800' }}>
                      {outputTotal.toLocaleString()}
                    </TableCell>
                    <TableCell align="center" sx={{ fontFamily: 'monospace', fontWeight: '800' }}>
                      {tokensTotal.toLocaleString()}
                    </TableCell>
                    <TableCell align="right" sx={{ fontWeight: '800', color: 'success.dark', fontSize: '0.95rem' }}>
                      ${costTotal.toFixed(4)}
                    </TableCell>
                    <TableCell align="left">
                      <Typography variant="caption" sx={{ fontWeight: '800' }}>100%</Typography>
                    </TableCell>
                  </TableRow>
                </TableBody>
              </Table>
            </TableContainer>
          </Box>
        )}

        {/* Tab 3: Rate Card Reference */}
        {activeTab === 'pricing' && (
          <Box>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              Standard unit pricing per 1,000,000 tokens applied for real-time cost calculation:
            </Typography>

            <TableContainer component={Paper} variant="outlined" sx={{ borderRadius: '12px', overflow: 'hidden' }}>
              <Table size="small">
                <TableHead sx={{ bgcolor: 'action.hover' }}>
                  <TableRow>
                    <TableCell sx={{ fontWeight: '700' }}>Model Name</TableCell>
                    <TableCell sx={{ fontWeight: '700' }}>Provider</TableCell>
                    <TableCell align="center" sx={{ fontWeight: '700' }}>Input Price / 1M</TableCell>
                    <TableCell align="center" sx={{ fontWeight: '700' }}>Output Price / 1M</TableCell>
                    <TableCell sx={{ fontWeight: '700' }}>Primary Use Case</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  <TableRow hover>
                    <TableCell sx={{ fontWeight: '600' }}>claude-sonnet-4-6</TableCell>
                    <TableCell>Anthropic</TableCell>
                    <TableCell align="center">$3.00</TableCell>
                    <TableCell align="center">$15.00</TableCell>
                    <TableCell>Defect Remediation & Technical Accessibility Guidance</TableCell>
                  </TableRow>
                  <TableRow hover>
                    <TableCell sx={{ fontWeight: '600' }}>gemini-3.5-flash</TableCell>
                    <TableCell>Google DeepMind</TableCell>
                    <TableCell align="center">$1.50</TableCell>
                    <TableCell align="center">$9.00</TableCell>
                    <TableCell>Test Case Synthesis & Rapid Criteria Mapping</TableCell>
                  </TableRow>
                  <TableRow hover>
                    <TableCell sx={{ fontWeight: '600' }}>gemini-3.5-flash-lite</TableCell>
                    <TableCell>Google DeepMind</TableCell>
                    <TableCell align="center">$0.30</TableCell>
                    <TableCell align="center">$2.50</TableCell>
                    <TableCell>Fast Element Classification</TableCell>
                  </TableRow>
                  <TableRow hover>
                    <TableCell sx={{ fontWeight: '600' }}>llama-3.1-8b-instant</TableCell>
                    <TableCell>Groq</TableCell>
                    <TableCell align="center">$0.05</TableCell>
                    <TableCell align="center">$0.08</TableCell>
                    <TableCell>High-Speed Fallback Reasoning</TableCell>
                  </TableRow>
                  <TableRow hover sx={{ bgcolor: 'action.hover' }}>
                    <TableCell sx={{ fontWeight: '600' }}>Cached Responses</TableCell>
                    <TableCell>In-Memory / Redis</TableCell>
                    <TableCell align="center">$0.00</TableCell>
                    <TableCell align="center">$0.00</TableCell>
                    <TableCell>Deterministic repeated element checks (Zero Cost)</TableCell>
                  </TableRow>
                </TableBody>
              </Table>
            </TableContainer>
          </Box>
        )}
      </DialogContent>

      {/* Modal Actions */}
      <DialogActions sx={{ px: 3, py: 2, bgcolor: 'action.hover', justifyContent: 'space-between' }}>
        <Typography variant="caption" color="text.secondary">
          All token quantities and dollar costs are computed in real-time from API response metadata.
        </Typography>
        <Button onClick={onClose} variant="contained" sx={{ borderRadius: '8px', fontWeight: '700' }}>
          Close
        </Button>
      </DialogActions>
    </Dialog>
  );
};
