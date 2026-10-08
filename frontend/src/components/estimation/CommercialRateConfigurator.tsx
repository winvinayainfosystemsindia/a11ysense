import React from 'react';
import {
  Box,
  Typography,
  Stack,
  Card,
  CardContent,
  Grid,
  TextField,
  Chip,
  InputAdornment,
  useTheme,
} from '@mui/material';
import { alpha } from '@mui/material/styles';
import RefreshIcon from '@mui/icons-material/Refresh';

interface CommercialRateConfiguratorProps {
  hourlyRate: number;
  platformFee: number;
  profitMarginPct: number;
  onRateChange: (hourlyRate: number, platformFee: number, profitMarginPct: number) => void;
}

export const CommercialRateConfigurator: React.FC<CommercialRateConfiguratorProps> = ({
  hourlyRate,
  platformFee,
  profitMarginPct,
  onRateChange,
}) => {
  const theme = useTheme();

  return (
    <Card
      sx={{
        mb: 4,
        borderRadius: 4,
        border: '1px solid',
        borderColor: theme.palette.divider,
        boxShadow: `0 2px 12px ${alpha(theme.palette.text.primary, 0.04)}`,
        bgcolor: theme.palette.background.paper,
      }}
    >
      <CardContent sx={{ p: 3 }}>
        <Stack
          component="div"
          direction={{ xs: 'column', sm: 'row' }}
          spacing={2}
          sx={{ justifyContent: 'space-between', alignItems: { xs: 'flex-start', sm: 'center' }, mb: 2 }}
        >
          <Box>
            <Typography
              variant="subtitle2"
              sx={{ fontWeight: 800, textTransform: 'uppercase', letterSpacing: '0.5px', color: theme.palette.text.primary }}
            >
              Commercial Rate Configuration (Live Recalculation)
            </Typography>
            <Typography variant="caption" color="text.secondary">
              Modify hourly auditor rates, platform fees, or margin markups to instantly adjust client proposals.
            </Typography>
          </Box>
          <Chip
            icon={<RefreshIcon />}
            label="Instant Recalculation"
            size="small"
            variant="outlined"
            color="primary"
            sx={{ fontWeight: 700 }}
          />
        </Stack>

        <Grid container spacing={3} component="div" sx={{ alignItems: 'center' }}>
          <Grid size={{ xs: 12, sm: 4 }} component="div">
            <TextField
              fullWidth
              size="small"
              type="number"
              label="Manual Auditor Hourly Rate ($)"
              value={hourlyRate}
              onChange={(e) => {
                const val = Number(e.target.value);
                onRateChange(val, platformFee, profitMarginPct);
              }}
              slotProps={{
                input: {
                  startAdornment: <InputAdornment position="start">$</InputAdornment>,
                },
              }}
              helperText="Assistive tech specialist verification fee"
            />
          </Grid>
          <Grid size={{ xs: 12, sm: 4 }} component="div">
            <TextField
              fullWidth
              size="small"
              type="number"
              label="Platform Fee per Page ($)"
              value={platformFee}
              onChange={(e) => {
                const val = Number(e.target.value);
                onRateChange(hourlyRate, val, profitMarginPct);
              }}
              slotProps={{
                input: {
                  startAdornment: <InputAdornment position="start">$</InputAdornment>,
                },
              }}
              helperText="Cloud orchestration & automated scanning"
            />
          </Grid>
          <Grid size={{ xs: 12, sm: 4 }} component="div">
            <TextField
              fullWidth
              size="small"
              type="number"
              label="Profit Margin Markup (%)"
              value={profitMarginPct}
              onChange={(e) => {
                const val = Number(e.target.value);
                onRateChange(hourlyRate, platformFee, val);
              }}
              slotProps={{
                input: {
                  endAdornment: <InputAdornment position="end">%</InputAdornment>,
                },
              }}
              helperText="Standard commercial agency margin"
            />
          </Grid>
        </Grid>
      </CardContent>
    </Card>
  );
};
