import React from 'react';
import { Card, Box, Typography, Stack, LinearProgress, alpha, useTheme } from '@mui/material';
import AutoAwesomeIcon from '@mui/icons-material/AutoAwesome';

interface CreditsBalanceCardProps {
  totalCredits: number;
  usedCredits: number;
}

const CreditsBalanceCard: React.FC<CreditsBalanceCardProps> = ({ totalCredits, usedCredits }) => {
  const theme = useTheme();
  const remainingCredits = totalCredits - usedCredits;
  const usagePercentage = (usedCredits / totalCredits) * 100;

  return (
    <Card variant="outlined" sx={{ p: 4, borderRadius: '16px', bgcolor: 'background.paper', position: 'relative', overflow: 'hidden' }}>
      <Box sx={{ position: 'absolute', top: -50, right: -50, width: '200px', height: '200px', bgcolor: alpha(theme.palette.primary.main, 0.05), borderRadius: '50%', pointerEvents: 'none' }} />
      <Box sx={{ position: 'absolute', bottom: -30, left: -30, width: '100px', height: '100px', bgcolor: alpha(theme.palette.secondary.main, 0.05), borderRadius: '50%', pointerEvents: 'none' }} />
      
      <Stack component="div" direction={{ xs: 'column', md: 'row' }} spacing={4} sx={{ justifyContent: 'space-between', alignItems: { xs: 'flex-start', md: 'center' } }}>
        <Box>
          <Stack component="div" direction="row" spacing={1} sx={{ alignItems: 'center', mb: 1 }}>
            <AutoAwesomeIcon color="primary" sx={{ fontSize: '1.2rem' }} />
            <Typography variant="overline" sx={{ fontWeight: '800', color: 'primary.main', letterSpacing: '1px' }}>
              AVAILABLE CREDITS
            </Typography>
          </Stack>
          <Typography variant="h2" sx={{ fontWeight: '800', mb: 1, letterSpacing: '-2px', color: 'text.primary' }}>
            {remainingCredits.toLocaleString()}
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Credits will roll over to the next billing cycle.
          </Typography>
        </Box>

        <Box sx={{ width: { xs: '100%', md: '40%' } }}>
          <Stack component="div" direction="row" sx={{ justifyContent: 'space-between', mb: 1 }}>
            <Typography variant="subtitle2" sx={{ fontWeight: '700' }}>
              Monthly Usage
            </Typography>
            <Typography variant="subtitle2" sx={{ fontWeight: '700', color: 'text.secondary' }}>
              {usedCredits.toLocaleString()} / {totalCredits.toLocaleString()}
            </Typography>
          </Stack>
          
          <LinearProgress 
            variant="determinate" 
            value={usagePercentage} 
            sx={{ 
              height: 12, 
              borderRadius: 6,
              bgcolor: alpha(theme.palette.primary.main, 0.1),
              '& .MuiLinearProgress-bar': {
                borderRadius: 6,
                backgroundImage: `linear-gradient(90deg, ${theme.palette.primary.main}, ${theme.palette.secondary.main})`
              }
            }} 
          />
          <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 1, textAlign: 'right', fontWeight: '500' }}>
            {usagePercentage.toFixed(1)}% used
          </Typography>
        </Box>
      </Stack>
    </Card>
  );
};

export default CreditsBalanceCard;
