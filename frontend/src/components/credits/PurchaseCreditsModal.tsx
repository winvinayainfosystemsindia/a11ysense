import React, { useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Typography,
  Box,
  IconButton,
  Grid,
  Card,
  alpha,
  useTheme
} from '@mui/material';
import CloseIcon from '@mui/icons-material/Close';
import AutoAwesomeIcon from '@mui/icons-material/AutoAwesome';

interface PurchaseCreditsModalProps {
  open: boolean;
  onClose: () => void;
  onPurchase: (amount: number) => void;
}

const creditPackages = [
  { amount: 10000, price: 49, popular: false },
  { amount: 50000, price: 199, popular: true },
  { amount: 200000, price: 599, popular: false },
];

const PurchaseCreditsModal: React.FC<PurchaseCreditsModalProps> = ({ open, onClose, onPurchase }) => {
  const theme = useTheme();
  const [selectedPackage, setSelectedPackage] = useState<number | null>(50000);

  const handlePurchase = () => {
    if (selectedPackage) {
      onPurchase(selectedPackage);
      setSelectedPackage(null);
      onClose();
    }
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle sx={{ m: 0, p: 2, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography variant="h6" sx={{ fontWeight: '700' }}>
          Purchase API Credits
        </Typography>
        <IconButton aria-label="close" onClick={onClose} sx={{ color: 'text.secondary' }}>
          <CloseIcon />
        </IconButton>
      </DialogTitle>
      <DialogContent dividers sx={{ p: 4, bgcolor: 'background.default' }}>
        <Typography variant="body1" color="text.secondary" sx={{ mb: 4, textAlign: 'center' }}>
          Select a credit package. Credits never expire and automatically apply to your usage.
        </Typography>

        <Grid container spacing={3}>
          {creditPackages.map((pkg) => (
            <Grid size={{ xs: 12, sm: 4 }} key={pkg.amount}>
              <Card
                variant="outlined"
                onClick={() => setSelectedPackage(pkg.amount)}
                sx={{
                  p: 3,
                  cursor: 'pointer',
                  textAlign: 'center',
                  borderRadius: '16px',
                  position: 'relative',
                  overflow: 'visible',
                  transition: 'all 0.2s ease-in-out',
                  borderColor: selectedPackage === pkg.amount ? 'primary.main' : 'divider',
                  bgcolor: selectedPackage === pkg.amount ? alpha(theme.palette.primary.main, 0.02) : 'background.paper',
                  boxShadow: selectedPackage === pkg.amount ? `0 8px 24px ${alpha(theme.palette.primary.main, 0.15)}` : 'none',
                  transform: selectedPackage === pkg.amount ? 'translateY(-4px)' : 'none',
                }}
              >
                {pkg.popular && (
                  <Box
                    sx={{
                      position: 'absolute',
                      top: -12,
                      left: '50%',
                      transform: 'translateX(-50%)',
                      bgcolor: 'primary.main',
                      color: 'primary.contrastText',
                      px: 2,
                      py: 0.5,
                      borderRadius: '12px',
                      fontSize: '0.75rem',
                      fontWeight: '800',
                      letterSpacing: '0.5px'
                    }}
                  >
                    MOST POPULAR
                  </Box>
                )}
                
                <AutoAwesomeIcon color={selectedPackage === pkg.amount ? 'primary' : 'disabled'} sx={{ fontSize: '2.5rem', mb: 2 }} />
                
                <Typography variant="h4" sx={{ fontWeight: '800', color: selectedPackage === pkg.amount ? 'primary.main' : 'text.primary' }}>
                  {pkg.amount.toLocaleString()}
                </Typography>
                <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 3 }}>
                  Credits
                </Typography>
                
                <Typography variant="h5" sx={{ fontWeight: '800' }}>
                  ${pkg.price}
                </Typography>
              </Card>
            </Grid>
          ))}
        </Grid>
      </DialogContent>
      <DialogActions sx={{ p: 3, justifyContent: 'center' }}>
        <Button onClick={onClose} sx={{ fontWeight: '600', color: 'text.secondary', mr: 2 }}>
          Cancel
        </Button>
        <Button
          onClick={handlePurchase}
          variant="contained"
          color="primary"
          disabled={!selectedPackage}
          size="large"
          sx={{ fontWeight: '700', borderRadius: '8px', px: 6 }}
        >
          Complete Purchase
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default PurchaseCreditsModal;
