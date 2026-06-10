import React from 'react';
import { Box, Typography, Stack } from '@mui/material';
import AdminPanelSettingsIcon from '@mui/icons-material/AdminPanelSettings';
import SecurityIcon from '@mui/icons-material/Security';
import { Button } from '../common/button';

interface DemoAccountsProps {
  onPrefill: (role: 'admin' | 'auditor') => void;
}

const DemoAccounts: React.FC<DemoAccountsProps> = ({ onPrefill }) => {
  return (
    <Box sx={{ 
      p: 1.5, 
      borderRadius: '8px', 
      bgcolor: 'background.default', 
      border: '1px dashed',
      borderColor: 'divider',
      textAlign: 'center'
    }}>
      <Typography component="span" variant="caption" color="text.secondary" sx={{ display: 'block', mb: 1, fontWeight: '600', letterSpacing: '0.5px', fontSize: '0.7rem' }}>
        DEVELOPER / DEMO ACCOUNTS
      </Typography>
      <Stack direction="row" spacing={1} sx={{ display: 'flex', justifyContent: 'center' }}>
        <Button 
          type="button" 
          variant="outlined" 
          size="small" 
          onClick={() => onPrefill('admin')}
          startIcon={<AdminPanelSettingsIcon sx={{ fontSize: '0.85rem !important' }} />}
          sx={{ 
            fontSize: '0.7rem', 
            py: 0.25, 
            px: 1,
            textTransform: 'none',
            borderColor: 'divider',
            color: 'text.secondary',
            borderRadius: '6px',
            '&:hover': {
              borderColor: 'text.disabled',
              backgroundColor: 'action.hover'
            }
          }}
        >
          Demo Admin
        </Button>
        <Button 
          type="button" 
          variant="outlined" 
          size="small" 
          onClick={() => onPrefill('auditor')}
          startIcon={<SecurityIcon sx={{ fontSize: '0.85rem !important' }} />}
          sx={{ 
            fontSize: '0.7rem', 
            py: 0.25, 
            px: 1,
            textTransform: 'none',
            borderColor: 'divider',
            color: 'text.secondary',
            borderRadius: '6px',
            '&:hover': {
              borderColor: 'text.disabled',
              backgroundColor: 'action.hover'
            }
          }}
        >
          Demo Auditor
        </Button>
      </Stack>
    </Box>
  );
};

export default DemoAccounts;
