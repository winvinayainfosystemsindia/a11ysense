import React from 'react';
import { Stack, Box, Typography, Button } from '@mui/material';
import KeyIcon from '@mui/icons-material/Key';
import AddIcon from '@mui/icons-material/Add';

interface ApiKeysHeaderProps {
  onGenerate: () => void;
}

const ApiKeysHeader: React.FC<ApiKeysHeaderProps> = ({ onGenerate }) => {
  return (
    <Stack
      component="div"
      direction={{ xs: 'column', md: 'row' }}
      spacing={2}
      sx={{ justifyContent: 'space-between', alignItems: { xs: 'flex-start', md: 'center' }, mb: 4 }}
    >
      <Box>
        <Stack component="div" direction="row" spacing={1.5} sx={{ alignItems: 'center' }}>
          <KeyIcon color="primary" sx={{ fontSize: '2rem' }} />
          <Typography variant="h4" sx={{ fontWeight: '800', color: 'text.primary', letterSpacing: '-0.5px' }}>
            API Keys
          </Typography>
        </Stack>
        <Typography variant="body2" color="text.secondary" sx={{ fontWeight: '500', mt: 0.5, pl: 0.5 }}>
          Manage your API keys for programmatic access to A11ySense AI services.
        </Typography>
      </Box>

      <Button
        variant="contained"
        color="primary"
        onClick={onGenerate}
        startIcon={<AddIcon />}
        sx={{
          fontWeight: '700',
          borderRadius: '8px',
          px: 3,
          py: 1
        }}
      >
        Generate New Key
      </Button>
    </Stack>
  );
};

export default ApiKeysHeader;
