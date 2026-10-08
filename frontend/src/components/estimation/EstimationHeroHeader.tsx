import React from 'react';
import {
  Box,
  Typography,
  Stack,
  Chip,
  Button,
  CircularProgress,
  useTheme,
} from '@mui/material';
import { alpha } from '@mui/material/styles';
import TuneIcon from '@mui/icons-material/Tune';
import FileDownloadIcon from '@mui/icons-material/FileDownload';
import DescriptionIcon from '@mui/icons-material/Description';
import PrintIcon from '@mui/icons-material/Print';
import type { EstimationResult } from '../../service/estimationService';

interface EstimationHeroHeaderProps {
  result: EstimationResult | null;
  exportingExcel: boolean;
  exportingPdf: boolean;
  onDownloadExcel: () => void;
  onDownloadPdf: () => void;
}

export const EstimationHeroHeader: React.FC<EstimationHeroHeaderProps> = ({
  result,
  exportingExcel,
  exportingPdf,
  onDownloadExcel,
  onDownloadPdf,
}) => {
  const theme = useTheme();

  return (
    <Box
      sx={{
        mb: 4,
        p: { xs: 3, md: 4 },
        borderRadius: 4,
        background: `linear-gradient(135deg, ${theme.palette.text.primary} 0%, ${theme.palette.primary.dark} 50%, #1e1b4b 100%)`,
        color: '#ffffff',
        position: 'relative',
        overflow: 'hidden',
        boxShadow: `0 12px 36px -4px ${alpha(theme.palette.common.black, 0.45)}`,
        border: `1px solid ${alpha('#ffffff', 0.1)}`,
      }}
    >
      <Stack
        component="div"
        direction={{ xs: 'column', md: 'row' }}
        spacing={3}
        sx={{ justifyContent: 'space-between', alignItems: { xs: 'flex-start', md: 'center' } }}
      >
        <Box sx={{ maxWidth: 760 }}>
          <Stack component="div" direction="row" spacing={1.5} sx={{ alignItems: 'center', mb: 1.5, flexWrap: 'wrap', gap: 1 }}>
            <Chip
              icon={<TuneIcon sx={{ fontSize: 16, color: `${theme.palette.secondary.light} !important` }} />}
              label="Commercial Scoping & Valuation Engine"
              size="small"
              sx={{
                bgcolor: alpha(theme.palette.secondary.main, 0.18),
                color: theme.palette.secondary.light,
                fontWeight: 700,
                fontSize: '0.75rem',
                border: `1px solid ${alpha(theme.palette.secondary.light, 0.35)}`,
              }}
            />
            <Chip
              label="WCAG 2.1 / 2.2 Auditing Standards"
              size="small"
              sx={{
                bgcolor: alpha('#ffffff', 0.1),
                color: theme.palette.grey[300],
                fontWeight: 600,
                fontSize: '0.75rem',
              }}
            />
          </Stack>
          <Typography
            variant="h3"
            sx={{
              fontWeight: 800,
              letterSpacing: '-0.025em',
              color: '#ffffff',
              mb: 1,
              fontSize: { xs: '1.75rem', md: '2.35rem' },
            }}
          >
            Accessibility Audit Estimation & Proposal Engine
          </Typography>
          <Typography
            variant="body1"
            sx={{ color: theme.palette.grey[300], lineHeight: 1.6, fontSize: { xs: '0.9rem', md: '1.025rem' } }}
          >
            Evaluate DOM complexity across Simple (1.0h), Medium (2.5h), and Complex (5.5h) tiers.
            Calculates manual verification hours, cloud scanning fees, and agency margin to produce client-ready commercial proposals.
          </Typography>
        </Box>

        {/* Quick Export Actions (When result is available) */}
        {result && (
          <Stack
            component="div"
            direction={{ xs: 'column', sm: 'row' }}
            spacing={1.5}
            sx={{ width: { xs: '100%', md: 'auto' } }}
          >
            <Button
              variant="contained"
              startIcon={
                exportingExcel ? <CircularProgress size={16} color="inherit" /> : <FileDownloadIcon />
              }
              onClick={onDownloadExcel}
              disabled={exportingExcel}
              sx={{
                bgcolor: theme.palette.success.main,
                color: '#ffffff',
                fontWeight: 700,
                borderRadius: 2,
                textTransform: 'none',
                px: 2.5,
                py: 1.2,
                boxShadow: `0 4px 14px ${alpha(theme.palette.success.main, 0.35)}`,
                '&:hover': {
                  bgcolor: theme.palette.success.dark,
                  transform: 'translateY(-1px)',
                },
                transition: 'all 0.2s cubic-bezier(0.16, 1, 0.3, 1)',
              }}
            >
              {exportingExcel ? 'Exporting...' : 'Excel Quote (.xlsx)'}
            </Button>
            <Button
              variant="contained"
              startIcon={
                exportingPdf ? <CircularProgress size={16} color="inherit" /> : <DescriptionIcon />
              }
              onClick={onDownloadPdf}
              disabled={exportingPdf}
              sx={{
                bgcolor: theme.palette.info.main,
                color: '#ffffff',
                fontWeight: 700,
                borderRadius: 2,
                textTransform: 'none',
                px: 2.5,
                py: 1.2,
                boxShadow: `0 4px 14px ${alpha(theme.palette.info.main, 0.35)}`,
                '&:hover': {
                  bgcolor: theme.palette.info.dark,
                  transform: 'translateY(-1px)',
                },
                transition: 'all 0.2s cubic-bezier(0.16, 1, 0.3, 1)',
              }}
            >
              {exportingPdf ? 'Exporting...' : 'PDF Proposal (.pdf)'}
            </Button>
            <Button
              variant="outlined"
              startIcon={<PrintIcon />}
              onClick={() => window.print()}
              sx={{
                borderColor: alpha('#ffffff', 0.25),
                color: theme.palette.grey[100],
                fontWeight: 700,
                borderRadius: 2,
                textTransform: 'none',
                '&:hover': {
                  borderColor: '#ffffff',
                  bgcolor: alpha('#ffffff', 0.08),
                },
              }}
            >
              Print
            </Button>
          </Stack>
        )}
      </Stack>
    </Box>
  );
};
