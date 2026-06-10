import React from 'react';
import { Card, Box, Typography, Button, Stack, alpha, useTheme } from '@mui/material';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';

interface CurrentPlanCardProps {
  planTier?: string;
  payAsYouGoEnabled?: boolean;
}

const CurrentPlanCard: React.FC<CurrentPlanCardProps> = ({ planTier = 'free', payAsYouGoEnabled }) => {
  const theme = useTheme();

  return (
    <Card variant="outlined" sx={{ p: 4, borderRadius: '16px', bgcolor: 'background.paper', position: 'relative', overflow: 'hidden' }}>
      <Box sx={{ position: 'absolute', top: 0, right: 0, width: '150px', height: '150px', bgcolor: alpha(theme.palette.primary.main, 0.05), borderRadius: '0 0 0 100%', pointerEvents: 'none' }} />
      
      <Stack component="div" direction={{ xs: 'column', md: 'row' }} spacing={4} sx={{ justifyContent: 'space-between', alignItems: { xs: 'flex-start', md: 'center' } }}>
        <Box>
          <Typography variant="overline" sx={{ fontWeight: '800', color: 'primary.main', letterSpacing: '1px' }}>
            CURRENT PLAN
          </Typography>
          <Typography variant="h3" sx={{ fontWeight: '800', mt: 1, mb: 1, letterSpacing: '-1px', textTransform: 'capitalize' }}>
            {planTier} Plan
          </Typography>
          <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
            {payAsYouGoEnabled ? 'Pay-As-You-Go Enabled (Overage allowed)' : 'Standard Billing (No overage)'}
          </Typography>

          <Stack component="div" spacing={1.5}>
            {['Unlimited Organization Members', 'Priority Distributed Scanning', 'Dedicated Support Representative', 'SSO & Advanced Security'].map((feature, i) => (
              <Box key={i} sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <CheckCircleIcon sx={{ color: 'success.main', fontSize: '1.2rem' }} />
                <Typography variant="body2" sx={{ fontWeight: '500' }}>{feature}</Typography>
              </Box>
            ))}
          </Stack>
        </Box>

        <Box sx={{ p: 3, border: '1px solid', borderColor: 'divider', borderRadius: '12px', bgcolor: alpha(theme.palette.background.default, 0.5), minWidth: { xs: '100%', md: '280px' } }}>
          <Typography variant="subtitle2" sx={{ fontWeight: '700', mb: 1 }}>
            Next Billing Date
          </Typography>
          <Typography variant="h5" sx={{ fontWeight: '800', mb: 0.5 }}>
            October 14, 2026
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
            Amount due: $3,588.00
          </Typography>
          
          <Button variant="contained" color="primary" fullWidth sx={{ fontWeight: '700', borderRadius: '8px', py: 1 }}>
            Manage Subscription
          </Button>
        </Box>
      </Stack>
    </Card>
  );
};

export default CurrentPlanCard;
