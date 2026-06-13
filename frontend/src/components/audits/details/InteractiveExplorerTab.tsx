import React from 'react';
import { Grid, Card, Stack, Typography, FormControl, InputLabel, Select, MenuItem, Chip, Box, IconButton, CircularProgress, Button, useTheme, alpha } from '@mui/material';
import BuildIcon from '@mui/icons-material/Build';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import CodeIcon from '@mui/icons-material/Code';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import { ViolationMockup } from './ViolationMockup';

interface InteractiveExplorerTabProps {
  taskId: string;
  filteredViolations: any[];
  selectedViolation: any;
  setSelectedViolation: (v: any) => void;
  severityFilter: string;
  setSeverityFilter: (s: string) => void;
  wcagFilter: string;
  setWcagFilter: (w: string) => void;
  wcagCriteriaList: string[];
  isApplyingFix: boolean;
  handleApplyFix: () => void;
  handleCopyCode: (code: string) => void;
}

export const InteractiveExplorerTab: React.FC<InteractiveExplorerTabProps> = ({
  taskId,
  filteredViolations,
  selectedViolation,
  setSelectedViolation,
  severityFilter,
  setSeverityFilter,
  wcagFilter,
  setWcagFilter,
  wcagCriteriaList,
  isApplyingFix,
  handleApplyFix,
  handleCopyCode
}) => {
  const theme = useTheme();

  return (
    <Grid container spacing={4}>
      {/* Left Column: Detected Violations */}
      <Grid size={{ xs: 12, md: 6 }}>
        <Card variant="outlined" sx={{ p: 3, borderRadius: '16px', display: 'flex', flexDirection: 'column', height: '100%', minHeight: '600px' }}>
          <Stack component="div" direction="row" sx={{ justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
            <Typography variant="h5" sx={{ fontWeight: '800', fontFamily: 'Outfit' }}>
              Detected Violations
            </Typography>
            
            {/* Filters */}
            <Stack component="div" direction="row" spacing={1.5}>
              <FormControl size="small" sx={{ minWidth: 130 }}>
                <InputLabel>Severity</InputLabel>
                <Select
                  value={severityFilter}
                  label="Severity"
                  onChange={(e) => setSeverityFilter(e.target.value)}
                  sx={{ borderRadius: '8px' }}
                >
                  <MenuItem value="all">All Severities</MenuItem>
                  <MenuItem value="critical">Critical</MenuItem>
                  <MenuItem value="serious">Serious</MenuItem>
                  <MenuItem value="moderate">Moderate</MenuItem>
                  <MenuItem value="minor">Minor</MenuItem>
                </Select>
              </FormControl>

              <FormControl size="small" sx={{ minWidth: 130 }}>
                <InputLabel>WCAG Rule</InputLabel>
                <Select
                  value={wcagFilter}
                  label="WCAG Rule"
                  onChange={(e) => setWcagFilter(e.target.value)}
                  sx={{ borderRadius: '8px' }}
                >
                  <MenuItem value="all">All WCAG</MenuItem>
                  {wcagCriteriaList.map((wcag) => (
                    <MenuItem key={wcag} value={wcag}>{wcag.split(' ')[0]}</MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Stack>
          </Stack>

          {/* Violations List */}
          <Stack component="div" spacing={2} sx={{ overflowY: 'auto', flex: 1, pr: 1, maxHeight: '550px' }}>
            {filteredViolations.map((v, idx) => {
              const isSelected = selectedViolation?.testcase_id === v.testcase_id;
              const sevColor = v.severity?.toLowerCase() === 'critical' ? 'error' : v.severity?.toLowerCase() === 'serious' ? 'warning' : 'info';
              return (
                <Box
                  key={v.testcase_id}
                  onClick={() => setSelectedViolation(v)}
                  sx={{
                    p: 2.5,
                    borderRadius: '12px',
                    border: `1px solid ${isSelected ? theme.palette.primary.main : '#e2e8f0'}`,
                    bgcolor: isSelected ? alpha(theme.palette.primary.main, 0.04) : '#ffffff',
                    cursor: 'pointer',
                    transition: 'all 0.2s',
                    position: 'relative',
                    '&:hover': {
                      borderColor: isSelected ? theme.palette.primary.main : '#cbd5e1',
                      bgcolor: isSelected ? alpha(theme.palette.primary.main, 0.06) : '#f8fafc',
                      transform: 'translateY(-1px)'
                    }
                  }}
                >
                  {isSelected && (
                    <Box sx={{ width: 4, height: '80%', bgcolor: 'primary.main', borderRadius: 2, position: 'absolute', left: 4, top: '10%' }} />
                  )}
                  <Stack component="div" direction="row" sx={{ justifyContent: 'space-between', alignItems: 'flex-start', mb: 1 }}>
                    <Chip
                      label={v.severity?.toUpperCase() || 'MODERATE'}
                      color={sevColor}
                      size="small"
                      sx={{ fontWeight: '800', fontSize: '0.65rem', height: '20px', borderRadius: '4px' }}
                    />
                    <Typography variant="caption" color="text.secondary" sx={{ fontWeight: '600' }}>
                      #{idx + 1}
                    </Typography>
                  </Stack>
                  <Typography variant="subtitle1" sx={{ fontWeight: '700', color: 'text.primary', mb: 0.5 }}>
                    {v.testcase_name}
                  </Typography>
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 1.5, display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
                    {v.description}
                  </Typography>
                  <Stack component="div" direction="row" spacing={1}>
                    <Chip label={v.criteria} size="small" variant="outlined" sx={{ fontWeight: '600', fontSize: '0.7rem', height: '20px' }} />
                    <Chip label={v.refined_by} size="small" sx={{ fontWeight: '600', fontSize: '0.7rem', height: '20px', bgcolor: '#f1f5f9' }} />
                  </Stack>
                </Box>
              );
            })}

            {filteredViolations.length === 0 && (
              <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', py: 8 }}>
                <CheckCircleIcon color="success" sx={{ fontSize: '3rem', mb: 1.5 }} />
                <Typography variant="h6" sx={{ fontWeight: '600' }}>No Violations Match Your Filters</Typography>
                <Typography variant="body2" color="text.secondary">All checked rules comply with WCAG standards.</Typography>
              </Box>
            )}
          </Stack>
        </Card>
      </Grid>

      {/* Right Column: Violation Context & AI Suggestion */}
      <Grid size={{ xs: 12, md: 6 }}>
        {selectedViolation ? (
          <Stack component="div" spacing={3}>
            {/* Visual Mockup Container */}
            <Card variant="outlined" sx={{ p: 3, borderRadius: '16px' }}>
              <Typography variant="subtitle2" sx={{ fontWeight: '800', color: 'text.secondary', mb: 2, textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                Violation Context
              </Typography>

              {selectedViolation.screenshot && selectedViolation.screenshot !== 'N/A' ? (
                <Box sx={{
                  border: '1px solid #cbd5e1',
                  borderRadius: '12px',
                  overflow: 'hidden',
                  bgcolor: '#ffffff',
                  boxShadow: '0 4px 6px -1px rgba(0,0,0,0.05)',
                  display: 'flex',
                  justifyContent: 'center',
                  alignItems: 'center'
                }}>
                  <img
                    src={`http://localhost:8002/report/${taskId}/screenshot/${selectedViolation.screenshot}`}
                    alt="Visual Evidence of Defect"
                    style={{ maxWidth: '100%', height: 'auto', display: 'block' }}
                  />
                </Box>
              ) : (
                <ViolationMockup htmlSnippet={selectedViolation.html_snippet} ruleId={selectedViolation.rule_id} />
              )}
              
              <Box sx={{ mt: 2 }}>
                <Typography variant="caption" color="text.secondary" sx={{ fontWeight: '700', display: 'block', mb: 0.5 }}>DOM LOCATION</Typography>
                <Typography variant="body2" sx={{ fontFamily: 'monospace', bgcolor: '#f1f5f9', p: 1.5, borderRadius: '8px', border: '1px solid #e2e8f0', wordBreak: 'break-all' }}>
                  {selectedViolation.page_title} &gt; {selectedViolation.rule_id}
                </Typography>
              </Box>
            </Card>

            {/* AI Fix Suggestion Panel */}
            <Card variant="outlined" sx={{ p: 3, borderRadius: '16px', bgcolor: '#0f172a', color: '#f8fafc', '&:hover': { transform: 'none' } }}>
              <Stack component="div" direction="row" sx={{ alignItems: 'center', gap: 1, mb: 2.5 }}>
                <BuildIcon sx={{ color: 'primary.light' }} />
                <Typography variant="subtitle2" sx={{ fontWeight: '800', color: 'primary.light', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                  AI Fix Suggestion (OpenClaw)
                </Typography>
              </Stack>

              <Stack component="div" spacing={2.5}>
                {/* Source Code Snippet */}
                <Box>
                  <Stack component="div" direction="row" sx={{ justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                    <Typography variant="caption" sx={{ color: 'text.disabled', fontWeight: '700' }}>VIOLATION CODE</Typography>
                    <IconButton size="small" onClick={() => handleCopyCode(selectedViolation.html_snippet)} sx={{ color: 'text.disabled', '&:hover': { color: '#ffffff' } }}>
                      <ContentCopyIcon fontSize="inherit" />
                    </IconButton>
                  </Stack>
                  <Box sx={{
                    p: 2,
                    borderRadius: '8px',
                    bgcolor: '#1e293b',
                    border: '1px solid #334155',
                    fontFamily: 'monospace',
                    fontSize: '0.8rem',
                    overflowX: 'auto',
                    maxHeight: 120,
                    whiteSpace: 'pre-wrap',
                    wordBreak: 'break-all',
                    color: '#fb7185'
                  }}>
                    {selectedViolation.html_snippet}
                  </Box>
                </Box>

                {/* Remediated Suggestion */}
                <Box>
                  <Stack component="div" direction="row" sx={{ justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                    <Typography variant="caption" sx={{ color: 'text.disabled', fontWeight: '700' }}>SUGGESTED FIX BY OPENCLAW</Typography>
                    <IconButton size="small" onClick={() => handleCopyCode(selectedViolation.remediation)} sx={{ color: 'text.disabled', '&:hover': { color: '#ffffff' } }}>
                      <ContentCopyIcon fontSize="inherit" />
                    </IconButton>
                  </Stack>
                  <Box sx={{
                    p: 2,
                    borderRadius: '8px',
                    bgcolor: '#1e293b',
                    border: '1px solid #334155',
                    fontFamily: 'monospace',
                    fontSize: '0.8rem',
                    overflowX: 'auto',
                    maxHeight: 120,
                    whiteSpace: 'pre-wrap',
                    wordBreak: 'break-all',
                    color: '#34d399'
                  }}>
                    {selectedViolation.remediation}
                  </Box>
                </Box>

                {/* Apply Fix Button */}
                <Box>
                  <Button
                    variant="contained"
                    color="success"
                    fullWidth
                    startIcon={isApplyingFix ? <CircularProgress size={18} color="inherit" /> : <CodeIcon />}
                    onClick={handleApplyFix}
                    disabled={isApplyingFix}
                    sx={{
                      bgcolor: 'success.main',
                      color: '#ffffff',
                      fontWeight: '700',
                      py: 1.25,
                      borderRadius: '8px',
                      textTransform: 'none',
                      '&:hover': { bgcolor: 'success.dark' }
                    }}
                  >
                    {isApplyingFix ? 'Applying Suggestion...' : 'Apply to Source Code'}
                  </Button>
                  <Typography variant="caption" sx={{ color: 'text.disabled', display: 'block', mt: 1, textAlign: 'center' }}>
                    Changes will be pushed via secure PR to your linked GitHub repository.
                  </Typography>
                </Box>
              </Stack>
            </Card>
          </Stack>
        ) : (
          <Card variant="outlined" sx={{ p: 4, borderRadius: '16px', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%', minHeight: '400px' }}>
            <Typography variant="body1" color="text.secondary" sx={{ fontStyle: 'italic' }}>
              Select a violation from the list to explore context and fixes.
            </Typography>
          </Card>
        )}
      </Grid>
    </Grid>
  );
};
