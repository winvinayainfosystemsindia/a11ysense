import React from 'react';
import { Box, Link as MuiLink } from '@mui/material';

const LegalFooter: React.FC = () => {
  return (
    <Box sx={{ display: 'flex', justifyContent: 'center', gap: 3, mt: 2 }}>
      <MuiLink href="#" sx={{ color: 'text.secondary', fontSize: '0.75rem', fontWeight: 500, textDecoration: 'none', '&:hover': { color: 'text.primary' } }}>
        Documentation
      </MuiLink>
      <MuiLink href="#" sx={{ color: 'text.secondary', fontSize: '0.75rem', fontWeight: 500, textDecoration: 'none', '&:hover': { color: 'text.primary' } }}>
        Privacy Policy
      </MuiLink>
      <MuiLink href="#" sx={{ color: 'text.secondary', fontSize: '0.75rem', fontWeight: 500, textDecoration: 'none', '&:hover': { color: 'text.primary' } }}>
        Security
      </MuiLink>
    </Box>
  );
};

export default LegalFooter;
