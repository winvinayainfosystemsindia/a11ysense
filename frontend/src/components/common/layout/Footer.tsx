import React from 'react';
import { useNavigate } from '@tanstack/react-router';
import { Box, Typography } from '@mui/material';

export const Footer: React.FC = () => {
  const navigate = useNavigate();

  return (
    <Box
      sx={{
        py: 3,
        px: { xs: 2, sm: 4 },
        borderTop: '1px solid',
        borderTopColor: 'divider',
        bgcolor: 'background.paper',
        display: 'flex',
        flexDirection: { xs: 'column', sm: 'row' },
        justifyContent: 'space-between',
        alignItems: 'center',
        gap: 2
      }}
    >
      <Typography variant="body2" color="text.secondary" sx={{ fontWeight: '500', fontSize: '0.82rem' }}>
        <strong>A11ySense AI</strong> © 2026 A11ySense AI. All rights reserved.
      </Typography>
      <Box sx={{ display: 'flex', gap: 3, flexWrap: 'wrap' }}>
        {['Documentation', 'Support', 'Privacy Policy', 'Terms of Service'].map((link) => (
          <Typography
            key={link}
            variant="body2"
            onClick={() => navigate({ to: '/maintenance' })}
            sx={{
              color: 'text.secondary',
              fontSize: '0.82rem',
              fontWeight: '600',
              cursor: 'pointer',
              '&:hover': { color: 'primary.main' }
            }}
          >
            {link}
          </Typography>
        ))}
      </Box>
    </Box>
  );
};
