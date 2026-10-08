import React from 'react';
import {
  Typography,
  Stack,
  Card,
  CardContent,
  Grid,
  useTheme,
} from '@mui/material';
import { alpha } from '@mui/material/styles';
import MonetizationOnIcon from '@mui/icons-material/MonetizationOn';
import AccessTimeIcon from '@mui/icons-material/AccessTime';
import LayersIcon from '@mui/icons-material/Layers';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import type { EstimationSummary } from '../../service/estimationService';

interface EstimationKpiCardsProps {
  summary: EstimationSummary;
}

export const EstimationKpiCards: React.FC<EstimationKpiCardsProps> = ({ summary }) => {
  const theme = useTheme();

  return (
    <Grid container spacing={3} component="div" sx={{ mb: 4 }}>
      {/* Total Final Quote (Hero Card) */}
      <Grid size={{ xs: 12, sm: 6, md: 3 }} component="div">
        <Card
          sx={{
            borderRadius: 4,
            background: `linear-gradient(135deg, ${theme.palette.text.primary} 0%, ${theme.palette.primary.dark} 70%, ${theme.palette.secondary.dark} 100%)`,
            color: '#ffffff',
            boxShadow: `0 10px 30px -5px ${alpha(theme.palette.primary.dark, 0.45)}`,
            border: `1px solid ${alpha('#ffffff', 0.12)}`,
            height: '100%',
          }}
        >
          <CardContent sx={{ p: 3 }}>
            <Stack component="div" direction="row" sx={{ justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
              <Typography variant="overline" sx={{ fontWeight: 800, letterSpacing: '1px', color: theme.palette.secondary.light }}>
                TOTAL QUOTED INVESTMENT
              </Typography>
              <MonetizationOnIcon sx={{ color: theme.palette.success.light }} />
            </Stack>
            <Typography variant="h3" sx={{ fontWeight: 800, color: theme.palette.success.light, letterSpacing: '-0.02em', mb: 0.5 }}>
              ${summary.total_final_cost.toFixed(2)}
            </Typography>
            <Typography variant="caption" sx={{ color: theme.palette.grey[300], display: 'block' }}>
              Base Cost + {summary.profit_margin_pct}% Agency Margin
            </Typography>
          </CardContent>
        </Card>
      </Grid>

      {/* Total Manual Hours */}
      <Grid size={{ xs: 12, sm: 6, md: 3 }} component="div">
        <Card
          sx={{
            borderRadius: 4,
            border: '1px solid',
            borderColor: theme.palette.divider,
            boxShadow: `0 4px 18px ${alpha(theme.palette.text.primary, 0.04)}`,
            bgcolor: theme.palette.background.paper,
            height: '100%',
          }}
        >
          <CardContent sx={{ p: 3 }}>
            <Stack component="div" direction="row" sx={{ justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
              <Typography variant="overline" color="text.secondary" sx={{ fontWeight: 800, letterSpacing: '1px' }}>
                MANUAL AUDIT EFFORT
              </Typography>
              <AccessTimeIcon color="action" />
            </Stack>
            <Typography variant="h3" sx={{ fontWeight: 800, color: theme.palette.primary.main, mb: 0.5 }}>
              {summary.total_manual_hours.toFixed(1)}{' '}
              <Typography component="span" variant="h5" color="text.secondary">
                hrs
              </Typography>
            </Typography>
            <Typography variant="caption" color="text.secondary" sx={{ display: 'block' }}>
              ${summary.total_manual_cost.toFixed(2)} @ ${summary.hourly_rate}/hr
            </Typography>
          </CardContent>
        </Card>
      </Grid>

      {/* Base Service Cost */}
      <Grid size={{ xs: 12, sm: 6, md: 3 }} component="div">
        <Card
          sx={{
            borderRadius: 4,
            border: '1px solid',
            borderColor: theme.palette.divider,
            boxShadow: `0 4px 18px ${alpha(theme.palette.text.primary, 0.04)}`,
            bgcolor: theme.palette.background.paper,
            height: '100%',
          }}
        >
          <CardContent sx={{ p: 3 }}>
            <Stack component="div" direction="row" sx={{ justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
              <Typography variant="overline" color="text.secondary" sx={{ fontWeight: 800, letterSpacing: '1px' }}>
                BASE SERVICE COST
              </Typography>
              <LayersIcon color="action" />
            </Stack>
            <Typography variant="h3" sx={{ fontWeight: 800, color: theme.palette.text.primary, mb: 0.5 }}>
              ${summary.total_base_cost.toFixed(2)}
            </Typography>
            <Typography variant="caption" color="text.secondary" sx={{ display: 'block' }}>
              API (${summary.total_api_cost.toFixed(2)}) + Platform (${summary.total_platform_cost.toFixed(2)})
            </Typography>
          </CardContent>
        </Card>
      </Grid>

      {/* Profit Margin */}
      <Grid size={{ xs: 12, sm: 6, md: 3 }} component="div">
        <Card
          sx={{
            borderRadius: 4,
            border: '1px solid',
            borderColor: theme.palette.divider,
            boxShadow: `0 4px 18px ${alpha(theme.palette.text.primary, 0.04)}`,
            bgcolor: theme.palette.background.paper,
            height: '100%',
          }}
        >
          <CardContent sx={{ p: 3 }}>
            <Stack component="div" direction="row" sx={{ justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
              <Typography variant="overline" color="text.secondary" sx={{ fontWeight: 800, letterSpacing: '1px' }}>
                NET PROFIT MARKUP ({summary.profit_margin_pct}%)
              </Typography>
              <TrendingUpIcon color="success" />
            </Stack>
            <Typography variant="h3" sx={{ fontWeight: 800, color: theme.palette.success.main, mb: 0.5 }}>
              ${summary.total_profit_margin.toFixed(2)}
            </Typography>
            <Typography variant="caption" color="text.secondary" sx={{ display: 'block' }}>
              Calculated on total base operational costs
            </Typography>
          </CardContent>
        </Card>
      </Grid>
    </Grid>
  );
};
