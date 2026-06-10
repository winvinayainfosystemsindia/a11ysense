import React from 'react';
import { Stack, Box, Typography, Button } from '@mui/material';
import PaymentIcon from '@mui/icons-material/Payment';

const BillingHeader: React.FC = () => {
  return (
    <Stack
      component="div"
      direction={{ xs: 'column', md: 'row' }}
      spacing={2}
      sx={{ justifyContent: 'space-between', alignItems: { xs: 'flex-start', md: 'center' }, mb: 4 }}
    >
      <Box>
        <Stack component="div" direction="row" spacing={1.5} sx={{ alignItems: 'center' }}>
          <PaymentIcon color="primary" sx={{ fontSize: '2rem' }} />
          <Typography variant="h4" sx={{ fontWeight: '800', color: 'text.primary', letterSpacing: '-0.5px' }}>
            Billing Management
          </Typography>
        </Stack>
        <Typography variant="body2" color="text.secondary" sx={{ fontWeight: '500', mt: 0.5, pl: 0.5 }}>
          Manage your subscription plans, payment methods, and billing history.
        </Typography>
      </Box>

      <Button
        variant="outlined"
        color="inherit"
        sx={{
          fontWeight: '700',
          borderRadius: '8px',
          px: 3,
          py: 1,
          borderColor: 'divider',
          '&:hover': { bgcolor: 'background.default' }
        }}
        onClick={() => window.open('mailto:support@a11ysense.ai')}
      >
        Contact Support
      </Button>
    </Stack>
  );
};

export default BillingHeader;
