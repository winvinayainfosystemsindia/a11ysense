import React from 'react';
import {
  Box,
  Typography,
  Stack,
  Card,
  CardContent,
  Grid,
  Button,
  Chip,
  Divider,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  IconButton,
  useTheme,
} from '@mui/material';
import { alpha } from '@mui/material/styles';
import CloseIcon from '@mui/icons-material/Close';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import SpeedIcon from '@mui/icons-material/Speed';
import DynamicFormIcon from '@mui/icons-material/DynamicForm';
import AutoAwesomeIcon from '@mui/icons-material/AutoAwesome';

interface ComplexityMatrixGuideProps {
  open: boolean;
  onClose: () => void;
}

interface TierFeature {
  label: string;
  detail: string;
}

interface TierCardData {
  id: string;
  badge: string;
  title: string;
  subtitle: string;
  hours: string;
  unit: string;
  targetPages: string;
  recommended?: boolean;
  colorType: 'success' | 'warning' | 'error';
  icon: React.ReactNode;
  features: TierFeature[];
  footerNote: string;
}

export const ComplexityMatrixGuide: React.FC<ComplexityMatrixGuideProps> = ({
  open,
  onClose,
}) => {
  const theme = useTheme();

  const tiers: TierCardData[] = [
    {
      id: 'simple',
      badge: 'TIER 1 · BASIC',
      title: 'Simple',
      subtitle: 'Static Informational Content',
      hours: '1.0',
      unit: 'hr / page',
      targetPages: 'Blogs, About Us, Privacy Policies, FAQs, Landing Pages',
      colorType: 'success',
      icon: <SpeedIcon sx={{ fontSize: 20 }} />,
      footerNote: 'Quick sweep · ~1 Story Point',
      features: [
        { label: 'DOM Density', detail: '≤ 50 visible elements (links/buttons ≤ 60)' },
        { label: 'Interactivity', detail: 'Linear read top-to-bottom with no state mutations' },
        { label: 'Semantic Structure', detail: 'Native HTML headings (H1–H6), paragraphs & lists' },
        { label: 'Controls & Media', detail: 'Plain push buttons, informative/decorative images' },
        { label: 'Audit Scope', detail: 'Rapid keyboard tab sweep + automated scan' },
      ],
    },
    {
      id: 'medium',
      badge: 'TIER 2 · MOST COMMON',
      title: 'Medium',
      subtitle: 'Standard Interactive Controls',
      hours: '2.5',
      unit: 'hrs / page',
      targetPages: 'Contact Forms, Account Login, Search Results, Service Catalogs',
      recommended: true,
      colorType: 'warning',
      icon: <DynamicFormIcon sx={{ fontSize: 20 }} />,
      footerNote: 'Standard verification · ~3 Story Points',
      features: [
        { label: 'DOM Density', detail: '51 to 90 visible elements (or navigation links > 60)' },
        { label: 'Form Controls', detail: 'Standard inputs, checkboxes, radios, select dropdowns' },
        { label: 'Expanding Menus', detail: 'Accordions, collapsible menus, and tab interfaces' },
        { label: 'Tables & Media', detail: 'Standard data table with headers, single audio/video embed' },
        { label: 'Audit Scope', detail: 'Full keyboard trap check + NVDA / VoiceOver testing' },
      ],
    },
    {
      id: 'complex',
      badge: 'TIER 3 · ADVANCED',
      title: 'Complex',
      subtitle: 'Dynamic State & Custom Widgets',
      hours: '5.5',
      unit: 'hrs / page',
      targetPages: 'Checkout Flows, Analytics Dashboards, Portals, Multi-Step Wizards',
      colorType: 'error',
      icon: <AutoAwesomeIcon sx={{ fontSize: 20 }} />,
      footerNote: 'Deep assistive tech audit · ~5–8 Story Points',
      features: [
        { label: 'DOM Density', detail: '> 90 elements or any single complex trigger present' },
        { label: 'Popups & Modals', detail: 'Active dialogs, cookie banners, and focus traps' },
        { label: 'Custom Widgets', detail: 'Sliders, date pickers, comboboxes, tree views' },
        { label: 'Workflows & Auth', detail: 'Multi-step steppers, OTP, passwords, CAPTCHA' },
        { label: 'Live Content', detail: 'Carousels, tickers, maps, canvas charts, sortable tables' },
        { label: 'Audit Scope', detail: 'Multi-screen reader audit (NVDA, JAWS, VoiceOver) + 400% zoom' },
      ],
    },
  ];

  const getColorPalette = (colorType: 'success' | 'warning' | 'error') => {
    switch (colorType) {
      case 'success':
        return {
          main: theme.palette.success.main,
          dark: theme.palette.success.dark,
          light: theme.palette.success.light,
          bg: alpha(theme.palette.success.main, 0.06),
          border: alpha(theme.palette.success.main, 0.3),
          chipBg: alpha(theme.palette.success.main, 0.1),
        };
      case 'warning':
        return {
          main: theme.palette.warning.main,
          dark: theme.palette.warning.dark,
          light: theme.palette.warning.light,
          bg: alpha(theme.palette.warning.main, 0.06),
          border: alpha(theme.palette.warning.main, 0.35),
          chipBg: alpha(theme.palette.warning.main, 0.1),
        };
      case 'error':
        return {
          main: theme.palette.error.main,
          dark: theme.palette.error.dark,
          light: theme.palette.error.light,
          bg: alpha(theme.palette.error.main, 0.06),
          border: alpha(theme.palette.error.main, 0.3),
          chipBg: alpha(theme.palette.error.main, 0.1),
        };
    }
  };

  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="lg"
      fullWidth
      slotProps={{
        paper: {
          sx: {
            borderRadius: 3,
            p: 0,
            overflow: 'hidden',
            bgcolor: theme.palette.background.paper,
            boxShadow: '0 20px 40px -10px rgba(15, 23, 42, 0.18)',
          },
        },
      }}
    >
      <DialogTitle
        sx={{
          px: { xs: 2.5, sm: 3 },
          pt: 2.5,
          pb: 1.5,
          borderBottom: '1px solid',
          borderColor: theme.palette.divider,
        }}
      >
        <Stack
          component="div"
          direction="row"
          sx={{ justifyContent: 'space-between', alignItems: 'center' }}
        >
          <Box>
            <Typography variant="h6" sx={{ fontWeight: 800, color: theme.palette.text.primary, lineHeight: 1.2 }}>
              Complexity Classification Standards
            </Typography>
            <Typography variant="caption" color="text.secondary">
              Overview of DOM complexity thresholds, interactive behaviors, and manual audit verification times.
            </Typography>
          </Box>
          <IconButton
            onClick={onClose}
            size="small"
            sx={{
              color: 'text.secondary',
              '&:hover': { color: 'text.primary', bgcolor: alpha(theme.palette.text.primary, 0.06) },
            }}
          >
            <CloseIcon fontSize="small" />
          </IconButton>
        </Stack>
      </DialogTitle>

      <DialogContent sx={{ px: { xs: 2, sm: 3 }, py: 2 }}>
        <Grid container spacing={2} component="div" sx={{ alignItems: 'stretch' }}>
          {tiers.map((tier) => {
            const pal = getColorPalette(tier.colorType);

            return (
              <Grid size={{ xs: 12, md: 4 }} key={tier.id} component="div">
                <Card
                  sx={{
                    height: '100%',
                    display: 'flex',
                    flexDirection: 'column',
                    borderRadius: 2.5,
                    border: '1.5px solid',
                    borderColor: tier.recommended ? pal.main : pal.border,
                    bgcolor: theme.palette.background.paper,
                    boxShadow: tier.recommended
                      ? `0 6px 18px -2px ${alpha(pal.main, 0.2)}`
                      : 'none',
                    position: 'relative',
                    overflow: 'hidden',
                  }}
                >
                  {/* Sleek top colored accent bar */}
                  <Box sx={{ height: 3.5, bgcolor: pal.main, width: '100%' }} />

                  <CardContent sx={{ p: 2, flexGrow: 1, display: 'flex', flexDirection: 'column' }}>
                    {/* Header Badge & Icon */}
                    <Stack
                      component="div"
                      direction="row"
                      sx={{ justifyContent: 'space-between', alignItems: 'center', mb: 1 }}
                    >
                      <Chip
                        label={tier.badge}
                        size="small"
                        sx={{
                          bgcolor: pal.chipBg,
                          color: pal.dark,
                          fontWeight: 800,
                          fontSize: '0.68rem',
                          height: 22,
                          letterSpacing: '0.4px',
                          border: `1px solid ${pal.border}`,
                        }}
                      />
                      <Box sx={{ color: pal.main, display: 'flex' }}>
                        {tier.icon}
                      </Box>
                    </Stack>

                    {/* Tier Name & Subtitle */}
                    <Typography
                      variant="subtitle1"
                      sx={{
                        fontWeight: 800,
                        color: theme.palette.text.primary,
                        letterSpacing: '-0.01em',
                        lineHeight: 1.2,
                      }}
                    >
                      {tier.title}
                    </Typography>
                    <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 1.25 }}>
                      {tier.subtitle}
                    </Typography>

                    {/* Compact Effort Hours Callout */}
                    <Box
                      sx={{
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center',
                        px: 1.5,
                        py: 0.85,
                        borderRadius: 1.5,
                        bgcolor: pal.bg,
                        border: `1px solid ${pal.border}`,
                        mb: 1.25,
                      }}
                    >
                      <Typography
                        variant="subtitle1"
                        sx={{
                          fontWeight: 800,
                          color: pal.dark,
                          letterSpacing: '-0.02em',
                          lineHeight: 1,
                        }}
                      >
                        {tier.hours}{' '}
                        <Typography component="span" variant="caption" sx={{ fontWeight: 700, color: pal.dark }}>
                          {tier.unit}
                        </Typography>
                      </Typography>
                      <Typography variant="caption" sx={{ color: pal.dark, fontWeight: 700, fontSize: '0.72rem' }}>
                        Manual Verification
                      </Typography>
                    </Box>

                    {/* Ideal Page Types compact box */}
                    <Typography
                      variant="caption"
                      sx={{
                        display: 'block',
                        bgcolor: alpha(theme.palette.background.default, 0.8),
                        border: `1px solid ${theme.palette.divider}`,
                        borderRadius: 1.5,
                        p: 1,
                        mb: 1.25,
                        lineHeight: 1.35,
                        color: 'text.secondary',
                        fontSize: '0.74rem',
                      }}
                    >
                      <Box component="span" sx={{ fontWeight: 700, color: 'text.primary', mr: 0.5 }}>
                        Ideal for:
                      </Box>
                      {tier.targetPages}
                    </Typography>

                    <Divider sx={{ my: 1, borderColor: theme.palette.divider }} />

                    {/* Criteria Checklist Header */}
                    <Typography
                      variant="caption"
                      sx={{
                        fontWeight: 800,
                        color: 'text.secondary',
                        textTransform: 'uppercase',
                        letterSpacing: '0.5px',
                        display: 'block',
                        mb: 0.85,
                        fontSize: '0.68rem',
                      }}
                    >
                      CLASSIFICATION CRITERIA:
                    </Typography>

                    {/* Compact Criteria List */}
                    <Stack component="div" spacing={0.85} sx={{ mb: 1.5, flexGrow: 1 }}>
                      {tier.features.map((feat, fIdx) => (
                        <Box
                          key={fIdx}
                          sx={{
                            display: 'flex',
                            alignItems: 'flex-start',
                            gap: 1,
                          }}
                        >
                          <CheckCircleIcon
                            sx={{
                              color: pal.main,
                              fontSize: 15,
                              mt: '2px',
                              flexShrink: 0,
                            }}
                          />
                          <Typography
                            variant="body2"
                            sx={{
                              fontSize: '0.76rem',
                              lineHeight: 1.35,
                              color: 'text.secondary',
                              m: 0,
                            }}
                          >
                            <Box
                              component="span"
                              sx={{
                                fontWeight: 700,
                                color: 'text.primary',
                                mr: 0.5,
                              }}
                            >
                              {feat.label}:
                            </Box>
                            {feat.detail}
                          </Typography>
                        </Box>
                      ))}
                    </Stack>

                    {/* Compact Card Footer Note */}
                    <Box
                      sx={{
                        pt: 1,
                        borderTop: `1px dashed ${theme.palette.divider}`,
                        textAlign: 'center',
                      }}
                    >
                      <Typography
                        variant="caption"
                        sx={{ fontWeight: 700, color: 'text.secondary', fontSize: '0.7rem' }}
                      >
                        {tier.footerNote}
                      </Typography>
                    </Box>
                  </CardContent>
                </Card>
              </Grid>
            );
          })}
        </Grid>
      </DialogContent>

      <DialogActions
        sx={{
          px: { xs: 2.5, sm: 3 },
          py: 1.5,
          borderTop: '1px solid',
          borderColor: theme.palette.divider,
        }}
      >
        <Button
          onClick={onClose}
          variant="contained"
          color="primary"
          size="small"
          sx={{ fontWeight: 700, borderRadius: 2, textTransform: 'none', px: 3, py: 0.75 }}
        >
          Close
        </Button>
      </DialogActions>
    </Dialog>
  );
};
