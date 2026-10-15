import React, { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
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
  useTheme
} from '@mui/material';
import SmartToyIcon from '@mui/icons-material/SmartToy';
import MonetizationOnIcon from '@mui/icons-material/MonetizationOn';
import MemoryIcon from '@mui/icons-material/Memory';
import BugReportIcon from '@mui/icons-material/BugReport';
import AssignmentTurnedInIcon from '@mui/icons-material/AssignmentTurnedIn';
import InfoOutlinedIcon from '@mui/icons-material/InfoOutlined';
import LayersIcon from '@mui/icons-material/Layers';
import type { TokenUsage } from '../../../service/auditService';

interface Props {
  tokenUsage?: TokenUsage | null;
}

export const LLMCostBreakdownCard: React.FC<Props> = ({ tokenUsage }) => {
  const theme = useTheme();
  const [activeSubTab, setActiveSubTab] = useState<'operation' | 'provider'>('operation');

  if (!tokenUsage) {
    return null;
  }

  const costTotal = tokenUsage.cost_usd_total ?? tokenUsage.totals?.cost_usd ?? tokenUsage.cost_estimate_usd ?? 0.0;
  const tokensTotal = tokenUsage.tokens_total ?? tokenUsage.totals?.total_tokens ?? 0;
  const callsTotal = tokenUsage.llm_calls ?? tokenUsage.totals?.calls ?? 0;

  // Don't render empty card if no tokens used
  if (tokensTotal === 0 && costTotal === 0) {
    return null;
  }

  const byProvider = tokenUsage.cost_by_provider || {};
  const byCategory = tokenUsage.cost_by_category || {};

  // Normalize operational categories
  const categoriesList = [
    {
      key: 'defect',
      label: byCategory['defect']?.label || 'Defect Remediation & Analysis',
      icon: <BugReportIcon fontSize="small" sx={{ color: theme.palette.error.main }} />,
      color: theme.palette.error.main,
      data: byCategory['defect'] || { calls: 0, input_tokens: 0, output_tokens: 0, total_tokens: 0, cost_usd: 0 }
    },
    {
      key: 'testcase',
      label: byCategory['testcase']?.label || 'Test Case Synthesis & Evaluation',
      icon: <AssignmentTurnedInIcon fontSize="small" sx={{ color: theme.palette.primary.main }} />,
      color: theme.palette.primary.main,
      data: byCategory['testcase'] || { calls: 0, input_tokens: 0, output_tokens: 0, total_tokens: 0, cost_usd: 0 }
    },
    {
      key: 'other',
      label: byCategory['other']?.label || 'Other Operations (Planning, Summary, Vision)',
      icon: <InfoOutlinedIcon fontSize="small" sx={{ color: theme.palette.warning.main }} />,
      color: theme.palette.warning.main,
      data: byCategory['other'] || { calls: 0, input_tokens: 0, output_tokens: 0, total_tokens: 0, cost_usd: 0 }
    }
  ];

  return (
    <Card
      sx={{
        borderRadius: '16px',
        border: '1px solid',
        borderColor: 'divider',
        background: 'linear-gradient(135deg, rgba(15, 23, 42, 0.03) 0%, rgba(30, 41, 59, 0.06) 100%)',
        overflow: 'hidden',
        boxShadow: '0 4px 20px rgba(0,0,0,0.04)'
      }}
    >
      {/* Header Banner */}
      <Box
        sx={{
          px: 3,
          py: 2,
          background: 'linear-gradient(90deg, #1e293b 0%, #334155 100%)',
          color: '#ffffff',
          display: 'flex',
          flexWrap: 'wrap',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: 2
        }}
      >
        <Stack component="div" direction="row" spacing={1.5} sx={{ alignItems: 'center' }}>
          <SmartToyIcon sx={{ color: '#38bdf8' }} />
          <Box>
            <Typography variant="subtitle1" sx={{ fontWeight: '700', lineHeight: 1.2 }}>
              AI & LLM Cost Breakdown
            </Typography>
            <Typography variant="caption" sx={{ color: '#94a3b8' }}>
              Real-time token consumption and USD expense per model and audit task
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
              fontWeight: '700',
              border: '1px solid rgba(74, 222, 128, 0.3)'
            }}
          />
          <Chip
            icon={<MemoryIcon sx={{ color: '#38bdf8 !important' }} />}
            label={`${tokensTotal.toLocaleString()} Tokens`}
            sx={{
              bgcolor: 'rgba(56, 189, 248, 0.15)',
              color: '#38bdf8',
              fontWeight: '600',
              border: '1px solid rgba(56, 189, 248, 0.3)'
            }}
          />
          <Chip
            label={`${callsTotal} Calls`}
            size="small"
            sx={{
              bgcolor: 'rgba(255, 255, 255, 0.1)',
              color: '#e2e8f0',
              fontWeight: '600'
            }}
          />
        </Stack>
      </Box>

      <CardContent sx={{ p: 3 }}>
        {/* Toggle Switch */}
        <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 2.5 }}>
          <Tabs
            value={activeSubTab}
            onChange={(_, val) => setActiveSubTab(val)}
            textColor="primary"
            indicatorColor="primary"
            sx={{ minHeight: '40px' }}
          >
            <Tab
              value="operation"
              label="Cost by Operation (Defects / Test Cases / Other)"
              icon={<LayersIcon fontSize="small" />}
              iconPosition="start"
              sx={{ fontWeight: '700', textTransform: 'none', minHeight: '40px', py: 1 }}
            />
            <Tab
              value="provider"
              label="Cost by AI Provider (Claude Sonnet / Gemini)"
              icon={<SmartToyIcon fontSize="small" />}
              iconPosition="start"
              sx={{ fontWeight: '700', textTransform: 'none', minHeight: '40px', py: 1 }}
            />
          </Tabs>
        </Box>

        {/* View 1: By Operation (Defects vs Testcases vs Other) */}
        {activeSubTab === 'operation' && (
          <Box>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              Breakdown of tokens and costs consumed for defect narrative refinement, test case synthesis, and platform planning.
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
                    <TableCell align="left" sx={{ fontWeight: '700', width: '180px' }}>Cost Share</TableCell>
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
                          <Stack component="div" direction="row" spacing={1} sx={{ alignItems: 'center' }}>
                            {cat.icon}
                            <Box>
                              <Typography variant="body2" sx={{ fontWeight: '600' }}>
                                {cat.label}
                              </Typography>
                              <Typography variant="caption" color="text.secondary">
                                {cat.key === 'defect'
                                  ? 'Root cause analysis, severity assessment & code remediation'
                                  : cat.key === 'testcase'
                                  ? 'Multi-agent test case synthesis & criteria validation'
                                  : 'Audit strategy, executive summary & vision parsing'}
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
                          <Typography variant="body2" sx={{ fontFamily: 'monospace', fontWeight: '600' }}>
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
                            <Box sx={{ width: '100px' }}>
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
                            <Typography variant="caption" sx={{ fontWeight: '600', color: 'text.secondary' }}>
                              {sharePct.toFixed(1)}%
                            </Typography>
                          </Stack>
                        </TableCell>
                      </TableRow>
                    );
                  })}
                  <TableRow sx={{ bgcolor: 'action.selected' }}>
                    <TableCell sx={{ fontWeight: '700' }}>Total (All Operations)</TableCell>
                    <TableCell align="center" sx={{ fontWeight: '700' }}>{callsTotal}</TableCell>
                    <TableCell align="center" sx={{ fontFamily: 'monospace', fontWeight: '700' }}>
                      {(tokenUsage.totals?.input_tokens ?? tokenUsage.tokens_sent ?? 0).toLocaleString()}
                    </TableCell>
                    <TableCell align="center" sx={{ fontFamily: 'monospace', fontWeight: '700' }}>
                      {(tokenUsage.totals?.output_tokens ?? tokenUsage.tokens_received ?? 0).toLocaleString()}
                    </TableCell>
                    <TableCell align="center" sx={{ fontFamily: 'monospace', fontWeight: '700' }}>
                      {tokensTotal.toLocaleString()}
                    </TableCell>
                    <TableCell align="right" sx={{ fontWeight: '800', color: 'success.dark', fontSize: '0.95rem' }}>
                      ${costTotal.toFixed(4)}
                    </TableCell>
                    <TableCell align="left">
                      <Typography variant="caption" sx={{ fontWeight: '700' }}>100%</Typography>
                    </TableCell>
                  </TableRow>
                </TableBody>
              </Table>
            </TableContainer>
          </Box>
        )}

        {/* View 2: By Provider (Claude Sonnet vs Gemini) */}
        {activeSubTab === 'provider' && (
          <Box>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              Independent token consumption and billable rates for Claude Sonnet ($3 in / $15 out per 1M) vs Gemini ($1.5 in / $9 out per 1M).
            </Typography>

            <TableContainer component={Paper} variant="outlined" sx={{ borderRadius: '12px', overflow: 'hidden' }}>
              <Table size="small">
                <TableHead sx={{ bgcolor: 'action.hover' }}>
                  <TableRow>
                    <TableCell sx={{ fontWeight: '700' }}>AI Provider</TableCell>
                    <TableCell align="center" sx={{ fontWeight: '700' }}>API Calls</TableCell>
                    <TableCell align="center" sx={{ fontWeight: '700' }}>Input Tokens</TableCell>
                    <TableCell align="center" sx={{ fontWeight: '700' }}>Output Tokens</TableCell>
                    <TableCell align="center" sx={{ fontWeight: '700' }}>Total Tokens</TableCell>
                    <TableCell align="right" sx={{ fontWeight: '700' }}>Cost (USD)</TableCell>
                    <TableCell align="left" sx={{ fontWeight: '700', width: '180px' }}>Cost Share</TableCell>
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
                          <Stack component="div" direction="row" spacing={1} sx={{ alignItems: 'center' }}>
                            <Box
                              sx={{
                                width: 10,
                                height: 10,
                                borderRadius: '50%',
                                bgcolor: color
                              }}
                            />
                            <Box>
                              <Typography variant="body2" sx={{ fontWeight: '600' }}>
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
                          <Typography variant="body2" sx={{ fontFamily: 'monospace', fontWeight: '600' }}>
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
                            <Box sx={{ width: '100px' }}>
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
                            <Typography variant="caption" sx={{ fontWeight: '600', color: 'text.secondary' }}>
                              {sharePct.toFixed(1)}%
                            </Typography>
                          </Stack>
                        </TableCell>
                      </TableRow>
                    );
                  })}
                  <TableRow sx={{ bgcolor: 'action.selected' }}>
                    <TableCell sx={{ fontWeight: '700' }}>Total (All Models)</TableCell>
                    <TableCell align="center" sx={{ fontWeight: '700' }}>{callsTotal}</TableCell>
                    <TableCell align="center" sx={{ fontFamily: 'monospace', fontWeight: '700' }}>
                      {(tokenUsage.totals?.input_tokens ?? tokenUsage.tokens_sent ?? 0).toLocaleString()}
                    </TableCell>
                    <TableCell align="center" sx={{ fontFamily: 'monospace', fontWeight: '700' }}>
                      {(tokenUsage.totals?.output_tokens ?? tokenUsage.tokens_received ?? 0).toLocaleString()}
                    </TableCell>
                    <TableCell align="center" sx={{ fontFamily: 'monospace', fontWeight: '700' }}>
                      {tokensTotal.toLocaleString()}
                    </TableCell>
                    <TableCell align="right" sx={{ fontWeight: '800', color: 'success.dark', fontSize: '0.95rem' }}>
                      ${costTotal.toFixed(4)}
                    </TableCell>
                    <TableCell align="left">
                      <Typography variant="caption" sx={{ fontWeight: '700' }}>100%</Typography>
                    </TableCell>
                  </TableRow>
                </TableBody>
              </Table>
            </TableContainer>
          </Box>
        )}
      </CardContent>
    </Card>
  );
};
