import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Stack,
  Chip,
  Button,
  Tooltip
} from '@mui/material';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import TrendingDownIcon from '@mui/icons-material/TrendingDown';
import TrendingFlatIcon from '@mui/icons-material/TrendingFlat';
import CompareArrowsIcon from '@mui/icons-material/CompareArrows';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import NewReleasesIcon from '@mui/icons-material/NewReleases';
import ReplayIcon from '@mui/icons-material/Replay';
import BugReportIcon from '@mui/icons-material/BugReport';

import { regressionService } from '../../../service/regressionService';
import type { RegressionSummary } from '../../../model/regression.model';
import { RunComparisonModal } from './RunComparisonModal';

interface Props {
  taskId: string;
}

export const RegressionSummaryBanner: React.FC<Props> = ({ taskId }) => {
  const [data, setData] = useState<RegressionSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [isCompareOpen, setIsCompareOpen] = useState(false);

  useEffect(() => {
    let isMounted = true;
    const fetchRegression = async () => {
      try {
        setLoading(true);
        const res = await regressionService.getRegressionSummary(taskId);
        if (isMounted) {
          setData(res);
        }
      } catch (err) {
        if (isMounted) setData(null);
      } finally {
        if (isMounted) setLoading(false);
      }
    };
    fetchRegression();
    return () => {
      isMounted = false;
    };
  }, [taskId]);

  if (loading || !data) {
    return null;
  }

  const isBaseline = !data.has_previous_run || data.run_number === 1;
  const isPositiveDelta = data.score_delta > 0;
  const isNegativeDelta = data.score_delta < 0;

  return (
    <>
      <Card
        sx={{
          mb: 3,
          background: 'linear-gradient(135deg, rgba(30, 41, 59, 0.9) 0%, rgba(15, 23, 42, 0.95) 100%)',
          border: '1px solid',
          borderColor: isBaseline ? 'primary.main' : isPositiveDelta ? 'success.main' : isNegativeDelta ? 'error.main' : 'divider',
          borderRadius: 2,
          boxShadow: '0 4px 20px rgba(0,0,0,0.25)'
        }}
      >
        <CardContent sx={{ py: 2.5, px: 3, '&:last-child': { pb: 2.5 } }}>
          <Stack
            component="div"
            direction={{ xs: 'column', md: 'row' }}
            spacing={2}
            sx={{
              alignItems: { xs: 'flex-start', md: 'center' },
              justifyContent: 'space-between'
            }}
          >
            {/* Left: Run Identity & Delta */}
            <Stack
              component="div"
              direction="row"
              spacing={2}
              sx={{ alignItems: 'center', flexWrap: 'wrap' }}
            >
              <Box>
                <Stack component="div" direction="row" spacing={1} sx={{ alignItems: 'center' }}>
                  <Typography variant="h6" sx={{ fontWeight: 800, color: '#f8fafc', letterSpacing: '-0.02em' }}>
                    Run #{data.run_number}
                  </Typography>
                  <Chip
                    label={isBaseline ? 'Baseline Run' : `Regression vs Run #${data.previous_run_number}`}
                    size="small"
                    color={isBaseline ? 'primary' : 'secondary'}
                    variant="outlined"
                    sx={{ fontWeight: 700, fontSize: '0.75rem' }}
                  />
                </Stack>
                <Typography variant="caption" sx={{ color: '#94a3b8' }}>
                  {isBaseline
                    ? 'Initial audit run establishing baseline defects and accessibility benchmark.'
                    : `Reconciliation against Run #${data.previous_run_number} (${data.previous_score}%)`}
                </Typography>
              </Box>

              {!isBaseline && (
                <Tooltip title={`Score changed from ${data.previous_score}% to ${data.score}%`}>
                  <Chip
                    icon={
                      isPositiveDelta ? (
                        <TrendingUpIcon sx={{ '&&': { color: '#22c55e' } }} />
                      ) : isNegativeDelta ? (
                        <TrendingDownIcon sx={{ '&&': { color: '#ef4444' } }} />
                      ) : (
                        <TrendingFlatIcon sx={{ '&&': { color: '#94a3b8' } }} />
                      )
                    }
                    label={`${isPositiveDelta ? '+' : ''}${data.score_delta}%`}
                    sx={{
                      fontWeight: 800,
                      fontSize: '0.85rem',
                      bgcolor: isPositiveDelta ? 'rgba(34, 197, 94, 0.15)' : isNegativeDelta ? 'rgba(239, 68, 68, 0.15)' : 'rgba(148, 163, 184, 0.15)',
                      color: isPositiveDelta ? '#4ade80' : isNegativeDelta ? '#f87171' : '#cbd5e1',
                      border: '1px solid',
                      borderColor: isPositiveDelta ? 'rgba(34, 197, 94, 0.3)' : isNegativeDelta ? 'rgba(239, 68, 68, 0.3)' : 'transparent'
                    }}
                  />
                </Tooltip>
              )}
            </Stack>

            {/* Middle: Defect Lifecycle Counters */}
            <Stack
              component="div"
              direction="row"
              spacing={1.5}
              sx={{ alignItems: 'center', flexWrap: 'wrap' }}
            >
              {!isBaseline && (
                <Chip
                  icon={<CheckCircleIcon sx={{ '&&': { color: '#22c55e' } }} />}
                  label={`${data.defects_fixed} Fixed`}
                  size="small"
                  sx={{
                    bgcolor: 'rgba(34, 197, 94, 0.12)',
                    color: '#86efac',
                    fontWeight: 700,
                    border: '1px solid rgba(34, 197, 94, 0.3)'
                  }}
                />
              )}

              <Chip
                icon={<NewReleasesIcon sx={{ '&&': { color: '#ef4444' } }} />}
                label={`${data.defects_new} New`}
                size="small"
                sx={{
                  bgcolor: 'rgba(239, 68, 68, 0.12)',
                  color: '#fca5a5',
                  fontWeight: 700,
                  border: '1px solid rgba(239, 68, 68, 0.3)'
                }}
              />

              {!isBaseline && data.defects_reopened > 0 && (
                <Chip
                  icon={<ReplayIcon sx={{ '&&': { color: '#f59e0b' } }} />}
                  label={`${data.defects_reopened} Reopened`}
                  size="small"
                  sx={{
                    bgcolor: 'rgba(245, 158, 11, 0.15)',
                    color: '#fcd34d',
                    fontWeight: 700,
                    border: '1px solid rgba(245, 158, 11, 0.3)'
                  }}
                />
              )}

              <Chip
                icon={<BugReportIcon sx={{ '&&': { color: '#38bdf8' } }} />}
                label={`${data.defects_open} Open`}
                size="small"
                sx={{
                  bgcolor: 'rgba(56, 189, 248, 0.12)',
                  color: '#7dd3fc',
                  fontWeight: 700,
                  border: '1px solid rgba(56, 189, 248, 0.3)'
                }}
              />

              {data.defects_not_retested > 0 && (
                <Tooltip title="Defects on pages not scanned in this run, or run did not complete successfully">
                  <Chip
                    label={`${data.defects_not_retested} Untested`}
                    size="small"
                    variant="outlined"
                    sx={{ color: '#94a3b8', borderColor: '#475569', fontSize: '0.75rem' }}
                  />
                </Tooltip>
              )}
            </Stack>

            {/* Right: Compare Action */}
            {!isBaseline && (
              <Button
                variant="outlined"
                size="small"
                startIcon={<CompareArrowsIcon />}
                onClick={() => setIsCompareOpen(true)}
                sx={{
                  color: '#f8fafc',
                  borderColor: 'rgba(255, 255, 255, 0.2)',
                  fontWeight: 600,
                  textTransform: 'none',
                  '&:hover': {
                    borderColor: 'primary.main',
                    bgcolor: 'rgba(59, 130, 246, 0.1)'
                  }
                }}
              >
                Compare with Run #{data.previous_run_number}
              </Button>
            )}
          </Stack>
        </CardContent>
      </Card>

      {/* Comparison Modal */}
      {isCompareOpen && (
        <RunComparisonModal
          open={isCompareOpen}
          onClose={() => setIsCompareOpen(false)}
          currentTaskId={taskId}
          previousTaskId={null}
        />
      )}
    </>
  );
};
