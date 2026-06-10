import React, { useState, useEffect } from 'react';
import { Box, Stack, Snackbar, Alert, Grid, CircularProgress, Typography } from '@mui/material';
import CreditsHeader from '../../components/credits/CreditsHeader';
import CreditsBalanceCard from '../../components/credits/CreditsBalanceCard';
import UsageChart from '../../components/credits/UsageChart';
import PurchaseCreditsModal from '../../components/credits/PurchaseCreditsModal';
import { billingService } from '../../service/billingService';
import type { BillingStatus } from '../../service/billingService';

const CreditsPage: React.FC = () => {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [snackbarMessage, setSnackbarMessage] = useState('');
  
  const [isLoading, setIsLoading] = useState(true);
  const [billingStatus, setBillingStatus] = useState<BillingStatus | null>(null);

  const fetchStatus = async () => {
    try {
      const data = await billingService.getBillingStatus();
      setBillingStatus(data);
    } catch (err) {
      console.error('Failed to fetch billing status', err);
      setSnackbarMessage('Error: Could not load credit balance from the server.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchStatus();
  }, []);

  const handlePurchase = async (amount: number) => {
    try {
      // package name resolution based on amount
      let packageName = 'starter';
      if (amount >= 30000) packageName = 'enterprise';
      else if (amount >= 6000) packageName = 'growth';

      // roughly estimating USD amount based on backend map
      let amountUsd = 10;
      if (packageName === 'growth') amountUsd = 50;
      if (packageName === 'enterprise') amountUsd = 200;

      await billingService.purchaseCredits(packageName, amountUsd);
      setSnackbarMessage(`Successfully purchased credits!`);
      // Refresh the status to get the updated balance and transactions
      fetchStatus();
    } catch (err) {
      console.error('Failed to purchase credits', err);
      setSnackbarMessage('Error: Purchase failed. Please try again.');
    }
  };

  // Calculate used credits from transactions if available
  const usedCredits = billingStatus?.transactions
    .filter(t => t.transaction_type === 'deduction' || t.transaction_type === 'usage')
    .reduce((acc, t) => acc + t.amount, 0) || 0;
  
  const currentBalance = billingStatus?.credit_balance || 0;
  // Total allocated for the period conceptually is balance + what was used
  const totalCredits = currentBalance + usedCredits;

  return (
    <Box sx={{ pb: 4 }}>
      <CreditsHeader onPurchase={() => setIsModalOpen(true)} />
      
      <Stack component="div" spacing={4} sx={{ mt: 4 }}>
        {isLoading ? (
          <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', py: 8 }}>
            <CircularProgress color="primary" />
            <Typography variant="body2" color="text.secondary" sx={{ mt: 2, fontWeight: '500' }}>
              Loading credit details...
            </Typography>
          </Box>
        ) : (
          <>
            <CreditsBalanceCard totalCredits={totalCredits} usedCredits={usedCredits} />
            
            <Grid container spacing={4}>
              <Grid size={{ xs: 12 }}>
                <UsageChart />
              </Grid>
            </Grid>
          </>
        )}
      </Stack>

      <PurchaseCreditsModal
        open={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onPurchase={handlePurchase}
      />

      <Snackbar
        open={!!snackbarMessage}
        autoHideDuration={4000}
        onClose={() => setSnackbarMessage('')}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert 
          severity={snackbarMessage.startsWith('Error') ? 'error' : 'success'} 
          sx={{ width: '100%', borderRadius: '8px', boxShadow: 3 }}
        >
          {snackbarMessage}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default CreditsPage;
