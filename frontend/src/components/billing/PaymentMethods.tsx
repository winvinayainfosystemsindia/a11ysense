import React from 'react';
import { Card, Box, Typography, Button, Stack, IconButton, alpha } from '@mui/material';
import CreditCardIcon from '@mui/icons-material/CreditCard';
import AddIcon from '@mui/icons-material/Add';
import DeleteIcon from '@mui/icons-material/Delete';

const PaymentMethods: React.FC = () => {
  return (
    <Card variant="outlined" sx={{ p: 3, borderRadius: '12px', bgcolor: 'background.paper', height: '100%' }}>
      <Stack component="div" direction="row" sx={{ justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h6" sx={{ fontWeight: '700' }}>
          Payment Methods
        </Typography>
        <Button size="small" startIcon={<AddIcon />} sx={{ fontWeight: '700' }}>
          Add Method
        </Button>
      </Stack>

      <Stack component="div" spacing={2}>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', p: 2, border: '1px solid', borderColor: 'primary.main', borderRadius: '8px', bgcolor: (theme) => alpha(theme.palette.primary.main, 0.03) }}>
          <Stack component="div" direction="row" spacing={2} sx={{ alignItems: 'center' }}>
            <Box sx={{ p: 1, bgcolor: 'background.paper', borderRadius: '4px', border: '1px solid', borderColor: 'divider', display: 'flex' }}>
              <CreditCardIcon color="primary" />
            </Box>
            <Box>
              <Typography variant="subtitle2" sx={{ fontWeight: '700' }}>
                Visa ending in 4242
              </Typography>
              <Typography variant="caption" color="text.secondary" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                Expires 12/28
                <Box component="span" sx={{ px: 0.75, py: 0.25, bgcolor: 'primary.main', color: 'primary.contrastText', borderRadius: '10px', fontSize: '0.6rem', fontWeight: '800' }}>DEFAULT</Box>
              </Typography>
            </Box>
          </Stack>
          <IconButton size="small" color="error">
            <DeleteIcon fontSize="small" />
          </IconButton>
        </Box>

        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', p: 2, border: '1px solid', borderColor: 'divider', borderRadius: '8px' }}>
          <Stack component="div" direction="row" spacing={2} sx={{ alignItems: 'center' }}>
            <Box sx={{ p: 1, bgcolor: 'background.default', borderRadius: '4px', border: '1px solid', borderColor: 'divider', display: 'flex' }}>
              <CreditCardIcon color="action" />
            </Box>
            <Box>
              <Typography variant="subtitle2" sx={{ fontWeight: '600' }}>
                Mastercard ending in 5555
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Expires 08/27
              </Typography>
            </Box>
          </Stack>
          <IconButton size="small" color="error">
            <DeleteIcon fontSize="small" />
          </IconButton>
        </Box>
      </Stack>
    </Card>
  );
};

export default PaymentMethods;
