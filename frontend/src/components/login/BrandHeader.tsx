import React from 'react';
import { Box, Typography } from '@mui/material';
import { alpha } from '@mui/material/styles';
import ChecklistIcon from '@mui/icons-material/Checklist';

const BrandHeader: React.FC = () => {
  return (
    <Box sx={{ mb: 2, display: 'flex', flexDirection: 'column', alignItems: 'center', textAlign: 'center' }}>
      <Box sx={{
        display: 'inline-flex',
        alignItems: 'center',
        justifyContent: 'center',
        width: 40,
        height: 40,
        borderRadius: '10px',
        bgcolor: 'primary.main',
        color: 'primary.contrastText',
        mb: 1,
        boxShadow: (theme) => `0 4px 12px ${alpha(theme.palette.primary.main, 0.2)}`
      }}>
        <ChecklistIcon sx={{ fontSize: 24 }} />
      </Box>
      <Typography variant="h5" component="h1" sx={{ 
        fontWeight: '800', 
        color: 'primary.main',
        letterSpacing: '-0.5px'
      }}>
        A11ySense AI
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ fontWeight: '500', mt: 0.25, fontSize: '0.825rem' }}>
        Inclusive by design. Accessible by default.
      </Typography>
    </Box>
  );
};

export default BrandHeader;
