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
  Collapse,
  useTheme,
} from '@mui/material';
import { alpha } from '@mui/material/styles';
import InfoOutlinedIcon from '@mui/icons-material/InfoOutlined';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import ExpandLessIcon from '@mui/icons-material/ExpandLess';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import SpeedIcon from '@mui/icons-material/Speed';
import DynamicFormIcon from '@mui/icons-material/DynamicForm';
import AutoAwesomeIcon from '@mui/icons-material/AutoAwesome';

interface ComplexityMatrixGuideProps {
  expanded: boolean;
  onToggle: () => void;
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
  effortCaption: string;
  targetPages: string;
  recommended?: boolean;
  colorType: 'success' | 'warning' | 'error';
  icon: React.ReactNode;
  features: TierFeature[];
  footerNote: string;
}

export const ComplexityMatrixGuide: React.FC<ComplexityMatrixGuideProps> = ({
  expanded,
  onToggle,
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
      effortCaption: 'Manual Assistive Tech Verification',
      targetPages: 'Blogs, About Us, Privacy Policies, FAQs, Landing Pages',
      colorType: 'success',
      icon: <SpeedIcon sx={{ fontSize: 24 }} />,
      footerNote: 'Quick sweep · ~1 Story Point',
      features: [
        { label: 'DOM Density', detail: '≤ 50 total visible elements (links & buttons ≤ 60)' },
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
      effortCaption: 'Manual Assistive Tech Verification',
      targetPages: 'Contact Forms, Account Login, Search Results, Service Catalogs',
      recommended: true,
      colorType: 'warning',
      icon: <DynamicFormIcon sx={{ fontSize: 24 }} />,
      footerNote: 'Standard verification · ~3 Story Points',
      features: [
        { label: 'DOM Density', detail: '51 to 90 visible elements (or navigation links > 60)' },
        { label: 'Form Controls', detail: 'Standard inputs, checkboxes, radios, select dropdowns' },
        { label: 'Expanding Navigation', detail: 'Accordions, collapsible menus, and tab interfaces' },
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
      effortCaption: 'Manual Assistive Tech Verification',
      targetPages: 'Checkout Flows, Analytics Dashboards, Portals, Multi-Step Wizards',
      colorType: 'error',
      icon: <AutoAwesomeIcon sx={{ fontSize: 24 }} />,
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
          bg: alpha(theme.palette.success.main, 0.05),
          border: alpha(theme.palette.success.main, 0.3),
          chipBg: alpha(theme.palette.success.main, 0.12),
        };
      case 'warning':
        return {
          main: theme.palette.warning.main,
          dark: theme.palette.warning.dark,
          light: theme.palette.warning.light,
          bg: alpha(theme.palette.warning.main, 0.05),
          border: alpha(theme.palette.warning.main, 0.35),
          chipBg: alpha(theme.palette.warning.main, 0.12),
        };
      case 'error':
        return {
          main: theme.palette.error.main,
          dark: theme.palette.error.dark,
          light: theme.palette.error.light,
          bg: alpha(theme.palette.error.main, 0.05),
          border: alpha(theme.palette.error.main, 0.3),
          chipBg: alpha(theme.palette.error.main, 0.12),
        };
    }
  };

  return (
    <Box sx={{ mb: 4 }}>
      {/* Collapsible Trigger Button */}
      <Button
        variant="text"
        color="inherit"
        onClick={onToggle}
        startIcon={<InfoOutlinedIcon color="primary" />}
        endIcon={expanded ? <ExpandLessIcon /> : <ExpandMoreIcon />}
        sx={{
          fontWeight: 700,
          textTransform: 'none',
          px: 0,
          mb: 1.5,
          color: theme.palette.text.primary,
          '&:hover': {
            bgcolor: 'transparent',
            color: theme.palette.primary.main,
          },
        }}
      >
        {expanded
          ? 'Hide Complexity Classification Guide'
          : 'View Complexity Classification Guide (Simple, Medium, Complex)'}
      </Button>

      <Collapse in={expanded}>
        <Box sx={{ mt: 1 }}>
          <Grid container spacing={3} component="div" sx={{ alignItems: 'stretch' }}>
            {tiers.map((tier) => {
              const pal = getColorPalette(tier.colorType);

              return (
                <Grid size={{ xs: 12, md: 4 }} key={tier.id} component="div">
                  <Card
                    sx={{
                      height: '100%',
                      display: 'flex',
                      flexDirection: 'column',
                      borderRadius: 4,
                      border: '2px solid',
                      borderColor: tier.recommended ? pal.main : pal.border,
                      bgcolor: theme.palette.background.paper,
                      boxShadow: tier.recommended
                        ? `0 12px 32px -4px ${alpha(pal.main, 0.25)}`
                        : `0 4px 20px -2px ${alpha(theme.palette.text.primary, 0.05)}`,
                      position: 'relative',
                      overflow: 'hidden',
                      transition: 'transform 0.2s ease, box-shadow 0.2s ease',
                      '&:hover': {
                        transform: 'translateY(-2px)',
                        boxShadow: `0 16px 36px -4px ${alpha(pal.main, 0.3)}`,
                      },
                    }}
                  >
                    {/* Top colored accent bar */}
                    <Box sx={{ height: 6, bgcolor: pal.main, width: '100%' }} />

                    <CardContent sx={{ p: { xs: 2.5, sm: 3 }, flexGrow: 1, display: 'flex', flexDirection: 'column' }}>
                      {/* Header Badge & Icon */}
                      <Stack
                        component="div"
                        direction="row"
                        sx={{ justifyContent: 'space-between', alignItems: 'center', mb: 2 }}
                      >
                        <Chip
                          label={tier.badge}
                          size="small"
                          sx={{
                            bgcolor: pal.chipBg,
                            color: pal.dark,
                            fontWeight: 800,
                            fontSize: '0.72rem',
                            letterSpacing: '0.5px',
                            border: `1px solid ${pal.border}`,
                          }}
                        />
                        <Box sx={{ color: pal.main, display: 'flex' }}>
                          {tier.icon}
                        </Box>
                      </Stack>

                      {/* Tier Name & Subtitle */}
                      <Typography
                        variant="h5"
                        sx={{
                          fontWeight: 800,
                          color: theme.palette.text.primary,
                          letterSpacing: '-0.01em',
                          mb: 0.5,
                        }}
                      >
                        {tier.title}
                      </Typography>
                      <Typography variant="body2" color="text.secondary" sx={{ mb: 2.5, minHeight: 40 }}>
                        {tier.subtitle}
                      </Typography>

                      {/* Effort Hours Callout */}
                      <Box
                        sx={{
                          p: 2,
                          borderRadius: 2.5,
                          bgcolor: pal.bg,
                          border: `1px solid ${pal.border}`,
                          mb: 2.5,
                        }}
                      >
                        <Stack component="div" direction="row" sx={{ alignItems: 'baseline', gap: 1 }}>
                          <Typography
                            variant="h3"
                            sx={{
                              fontWeight: 800,
                              color: pal.dark,
                              letterSpacing: '-0.03em',
                              lineHeight: 1,
                            }}
                          >
                            {tier.hours}
                          </Typography>
                          <Typography variant="subtitle2" sx={{ fontWeight: 700, color: pal.dark }}>
                            {tier.unit}
                          </Typography>
                        </Stack>
                        <Typography
                          variant="caption"
                          sx={{ display: 'block', mt: 0.75, color: pal.dark, fontWeight: 600 }}
                        >
                          {tier.effortCaption}
                        </Typography>
                      </Box>

                      {/* Best Suited For box */}
                      <Box sx={{ mb: 2.5 }}>
                        <Typography
                          variant="caption"
                          sx={{
                            fontWeight: 800,
                            color: 'text.secondary',
                            textTransform: 'uppercase',
                            letterSpacing: '0.5px',
                            display: 'block',
                            mb: 0.5,
                          }}
                        >
                          IDEAL PAGE TYPES:
                        </Typography>
                        <Typography
                          variant="body2"
                          sx={{
                            color: theme.palette.text.primary,
                            bgcolor: alpha(theme.palette.background.default, 0.9),
                            p: 1.25,
                            borderRadius: 1.5,
                            border: `1px solid ${theme.palette.divider}`,
                            fontSize: '0.825rem',
                            lineHeight: 1.5,
                          }}
                        >
                          {tier.targetPages}
                        </Typography>
                      </Box>

                      <Divider sx={{ my: 1.5 }} />

                      {/* Feature Checklist */}
                      <Typography
                        variant="caption"
                        sx={{
                          fontWeight: 800,
                          color: 'text.secondary',
                          textTransform: 'uppercase',
                          letterSpacing: '0.5px',
                          display: 'block',
                          mb: 1.5,
                        }}
                      >
                        CLASSIFICATION CRITERIA:
                      </Typography>

                      <Stack component="div" spacing={1.5} sx={{ mb: 3, flexGrow: 1 }}>
                        {tier.features.map((feat, fIdx) => (
                          <Box
                            key={fIdx}
                            sx={{
                              display: 'flex',
                              alignItems: 'flex-start',
                              gap: 1.25,
                            }}
                          >
                            <CheckCircleIcon
                              sx={{
                                color: pal.main,
                                fontSize: 17,
                                mt: '1px',
                                flexShrink: 0,
                              }}
                            />
                            <Typography
                              variant="body2"
                              sx={{
                                fontSize: '0.8125rem',
                                lineHeight: 1.45,
                                color: 'text.secondary',
                                m: 0,
                              }}
                            >
                              <Box
                                component="span"
                                sx={{
                                  fontWeight: 700,
                                  color: 'text.primary',
                                  mr: 0.75,
                                }}
                              >
                                {feat.label}:
                              </Box>
                              {feat.detail}
                            </Typography>
                          </Box>
                        ))}
                      </Stack>

                      {/* Card Footer Note */}
                      <Box
                        sx={{
                          pt: 1.5,
                          borderTop: `1px dashed ${theme.palette.divider}`,
                          textAlign: 'center',
                        }}
                      >
                        <Typography
                          variant="caption"
                          sx={{ fontWeight: 700, color: 'text.secondary' }}
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
        </Box>
      </Collapse>
    </Box>
  );
};
