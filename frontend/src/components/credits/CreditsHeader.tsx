import React from 'react';
import { Stack, Box, Typography, Button } from '@mui/material';
import AccountBalanceWalletIcon from '@mui/icons-material/AccountBalanceWallet';
import AddShoppingCartIcon from '@mui/icons-material/AddShoppingCart';

interface CreditsHeaderProps {
  onPurchase: () => void;
}

const CreditsHeader: React.FC<CreditsHeaderProps> = ({ onPurchase }) => {
  return (
    <Stack
      component="div"
      direction={{ xs: 'column', md: 'row' }}
      spacing={2}
      sx={{ justifyContent: 'space-between', alignItems: { xs: 'flex-start', md: 'center' }, mb: 4 }}
    >
      <Box>
        <Stack component="div" direction="row" spacing={1.5} sx={{ alignItems: 'center' }}>
          <AccountBalanceWalletIcon color="primary" sx={{ fontSize: '2rem' }} />
          <Typography variant="h4" sx={{ fontWeight: '800', color: 'text.primary', letterSpacing: '-0.5px' }}>
            Credits Balance
          </Typography>
        </Stack>
        <Typography variant="body2" color="text.secondary" sx={{ fontWeight: '500', mt: 0.5, pl: 0.5 }}>
          Monitor your API credit usage and purchase additional credits.
        </Typography>
      </Box>

      <Button
        variant="contained"
        color="primary"
        onClick={onPurchase}
        startIcon={<AddShoppingCartIcon />}
        sx={{
          fontWeight: '700',
          borderRadius: '8px',
          px: 3,
          py: 1
        }}
      >
        Buy Credits
      </Button>
    </Stack>
  );
};

export default CreditsHeader;
