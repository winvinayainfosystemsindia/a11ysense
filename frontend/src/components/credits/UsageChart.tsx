import React from 'react';
import { Card, Typography, Box, alpha, useTheme } from '@mui/material';

const UsageChart: React.FC = () => {
  const theme = useTheme();
  
  // Generating mock data for a 30-day bar chart
  const mockDays = Array.from({ length: 30 }, () => {
    const height = Math.random() * 80 + 20; // Random height between 20% and 100%
    return height;
  });

  return (
    <Card variant="outlined" sx={{ p: 3, borderRadius: '12px', bgcolor: 'background.paper', height: '100%', display: 'flex', flexDirection: 'column' }}>
      <Typography variant="h6" sx={{ fontWeight: '700', mb: 3 }}>
        Usage Over Last 30 Days
      </Typography>
      
      <Box sx={{ flexGrow: 1, display: 'flex', alignItems: 'flex-end', gap: { xs: 0.5, sm: 1 }, height: '200px', pt: 2, borderBottom: '1px solid', borderColor: 'divider' }}>
        {mockDays.map((height, index) => (
          <Box
            key={index}
            sx={{
              flexGrow: 1,
              height: `${height}%`,
              bgcolor: alpha(theme.palette.primary.main, 0.4),
              borderRadius: '4px 4px 0 0',
              transition: 'all 0.2s',
              cursor: 'pointer',
              '&:hover': {
                bgcolor: theme.palette.primary.main,
                transform: 'scaleY(1.05)',
                transformOrigin: 'bottom'
              }
            }}
          />
        ))}
      </Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 1 }}>
        <Typography variant="caption" color="text.secondary">30 Days Ago</Typography>
        <Typography variant="caption" color="text.secondary">Today</Typography>
      </Box>
    </Card>
  );
};

export default UsageChart;
