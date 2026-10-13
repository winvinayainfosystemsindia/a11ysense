import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Stack,
  Button,
  useTheme,
  Alert,
} from '@mui/material';
import { alpha } from '@mui/material/styles';
import { useParams, useNavigate } from '@tanstack/react-router';
import AddIcon from '@mui/icons-material/Add';
import InfoOutlinedIcon from '@mui/icons-material/InfoOutlined';
import Tooltip from '@mui/material/Tooltip';

import { estimationService } from '../../service/estimationService';
import type { SavedEstimateRecord } from '../../service/estimationService';

import {
  ComplexityMatrixGuide,
  CreateEstimateModal,
  EstimatesListTable,
} from '../../components/estimation';

export const EstimationPage: React.FC = () => {
  const theme = useTheme();
  const navigate = useNavigate();
  const { orgId } = useParams({ strict: false }) as any;

  const [estimates, setEstimates] = useState<SavedEstimateRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Modal dialog states
  const [openCreateModal, setOpenCreateModal] = useState(false);
  const [showCriteriaGuide, setShowCriteriaGuide] = useState(false);

  const fetchEstimates = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await estimationService.list(orgId);
      setEstimates(data);
    } catch (err: any) {
      console.error('Failed to load estimations:', err);
      setError(err?.response?.data?.detail || err?.message || 'Failed to fetch estimations.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchEstimates();
  }, [orgId]);

  const handleEstimateCreated = (estimateId: string) => {
    setOpenCreateModal(false);
    fetchEstimates();
    navigate({ to: `/org/${orgId}/estimation/${estimateId}` });
  };

  return (
    <Box sx={{ pb: 4 }}>
      {/* ── Page Header (Consistent with Audits and Projects pages) ── */}
      <Stack
        component="div"
        direction={{ xs: 'column', md: 'row' }}
        sx={{
          justifyContent: 'space-between',
          alignItems: { xs: 'flex-start', md: 'center' },
          mb: 4,
          gap: 2,
        }}
      >
        <Box sx={{ flex: 1, width: '100%' }}>
          <Stack
            component="div"
            direction="row"
            sx={{
              justifyContent: 'space-between',
              alignItems: 'center',
              mb: 0.5,
              flexWrap: 'wrap',
              gap: 1.5,
            }}
          >
            <Typography
              variant="h4"
              sx={{ fontWeight: 800, letterSpacing: '-0.5px' }}
            >
              Estimation
            </Typography>

            {/* Header Action Buttons: Complexity Guide + Create Estimate */}
            <Stack component="div" direction="row" spacing={1.5} sx={{ alignItems: 'center' }}>
              <Tooltip title="View Complexity Classification Guide">
                <Button
                  variant="outlined"
                  color="inherit"
                  size="small"
                  startIcon={<InfoOutlinedIcon color="primary" />}
                  onClick={() => setShowCriteriaGuide(true)}
                  sx={{
                    fontWeight: 700,
                    textTransform: 'none',
                    borderRadius: 2,
                    borderColor: theme.palette.divider,
                    bgcolor: theme.palette.background.paper,
                    color: theme.palette.text.primary,
                    boxShadow: '0 1px 3px rgba(0,0,0,0.04)',
                    '&:hover': {
                      borderColor: theme.palette.primary.main,
                      bgcolor: alpha(theme.palette.primary.main, 0.04),
                    },
                  }}
                >
                  Complexity Guide
                </Button>
              </Tooltip>

              <Button
                variant="contained"
                color="primary"
                size="small"
                startIcon={<AddIcon />}
                onClick={() => setOpenCreateModal(true)}
                sx={{
                  fontWeight: 700,
                  textTransform: 'none',
                  borderRadius: 2,
                  boxShadow: '0 2px 8px rgba(0,0,0,0.12)',
                }}
              >
                Create Estimate
              </Button>
            </Stack>
          </Stack>

          <Typography variant="body1" color="text.secondary">
            Evaluate page complexity across Simple, Medium, and Complex tiers to generate commercial audit proposals.
          </Typography>
        </Box>
      </Stack>

      {/* Error Banner */}
      {error && (
        <Alert severity="error" sx={{ mb: 3, borderRadius: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* ── Main Body: List of Estimations Table ── */}
      <EstimatesListTable
        estimates={estimates}
        loading={loading}
        onViewDetails={(id) => navigate({ to: `/org/${orgId}/estimation/${id}` })}
        onOpenCreate={() => setOpenCreateModal(true)}
        onRefresh={fetchEstimates}
      />

      {/* ── Stepper Modal: Create Estimate ── */}
      <CreateEstimateModal
        open={openCreateModal}
        onClose={() => setOpenCreateModal(false)}
        onSuccess={handleEstimateCreated}
        orgId={orgId}
      />

      {/* ── Complexity Standards Modal Dialog ── */}
      <ComplexityMatrixGuide
        open={showCriteriaGuide}
        onClose={() => setShowCriteriaGuide(false)}
      />
    </Box>
  );
};

export default EstimationPage;
