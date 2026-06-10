import React, { useState, useEffect } from 'react';
import { Box, Stack, Grid, CircularProgress, Typography } from '@mui/material';
import BillingHeader from '../../components/billing/BillingHeader';
import CurrentPlanCard from '../../components/billing/CurrentPlanCard';
import PaymentMethods from '../../components/billing/PaymentMethods';
import BillingHistoryTable from '../../components/billing/BillingHistoryTable';
import { billingService } from '../../service/billingService';
import type { BillingStatus } from '../../service/billingService';

const BillingPage: React.FC = () => {
  const [billingStatus, setBillingStatus] = useState<BillingStatus | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const data = await billingService.getBillingStatus();
        setBillingStatus(data);
      } catch (err) {
        console.error('Failed to fetch billing status', err);
      } finally {
        setIsLoading(false);
      }
    };
    fetchStatus();
  }, []);

  return (
    <Box sx={{ pb: 4 }}>
      <BillingHeader />
      
      <Stack component="div" spacing={4}>
        {isLoading ? (
          <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', py: 8 }}>
            <CircularProgress color="primary" />
            <Typography variant="body2" color="text.secondary" sx={{ mt: 2, fontWeight: '500' }}>
              Loading billing details...
            </Typography>
          </Box>
        ) : (
          <>
            <CurrentPlanCard planTier={billingStatus?.plan_tier} payAsYouGoEnabled={billingStatus?.pay_as_you_go_enabled} />
            
            <Grid container spacing={4}>
              <Grid size={{ xs: 12, md: 5 }}>
                <PaymentMethods />
              </Grid>
              <Grid size={{ xs: 12, md: 7 }}>
                <BillingHistoryTable transactions={billingStatus?.transactions || []} />
              </Grid>
            </Grid>
          </>
        )}
      </Stack>
    </Box>
  );
};

export default BillingPage;
