import React from 'react';
import { Box, Typography, Stack, useTheme } from '@mui/material';
import { alpha } from '@mui/material/styles';
import ChecklistIcon from '@mui/icons-material/Checklist';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';

const ShowcasePanel: React.FC = () => {
  const theme = useTheme();

  return (
    <Box sx={{
      height: '100%',
      display: 'flex',
      flexDirection: 'column',
      justifyContent: 'space-between',
      p: { xs: 4, md: 5 },
      position: 'relative',
      overflow: 'hidden'
    }}>
      {/* Background glow effects */}
      <Box sx={{
        position: 'absolute',
        top: '-10%',
        left: '-10%',
        width: '50%',
        height: '50%',
        borderRadius: '50%',
        background: `radial-gradient(circle, ${alpha(theme.palette.primary.light, 0.1)} 0%, transparent 70%)`,
        filter: 'blur(40px)',
        zIndex: 0
      }} />

      {/* Brand Header */}
      <Box sx={{ zIndex: 1, position: 'relative' }}>
        <Stack direction="row" spacing={1.5} sx={{ mb: 4, alignItems: 'center' }}>
          <Box sx={{
            display: 'inline-flex',
            alignItems: 'center',
            justifyContent: 'center',
            width: 36,
            height: 36,
            borderRadius: '8px',
            bgcolor: 'primary.main',
            color: 'primary.contrastText',
            boxShadow: `0 4px 12px ${alpha(theme.palette.primary.main, 0.3)}`
          }}>
            <ChecklistIcon sx={{ fontSize: 20 }} />
          </Box>
          <Typography variant="h6" sx={{ 
            fontWeight: 800, 
            letterSpacing: '-0.5px'
          }}>
            A11ySense AI
          </Typography>
        </Stack>

        {/* Copywriting */}
        <Typography variant="h4" component="h2" sx={{ 
          fontWeight: 800, 
          lineHeight: 1.25,
          mb: 2,
          letterSpacing: '-1px'
        }}>
          Enterprise-Grade Accessibility Auditing.
        </Typography>
        <Typography variant="body2" sx={{ color: 'text.disabled', mb: 3, lineHeight: 1.5, maxWidth: 420, fontSize: '0.85rem' }}>
          Automate your compliance workflow with our AI-powered auditing platform. Real-time scanning, remediation recommendations, and developer tracing in one workspace.
        </Typography>

        {/* Bullet feature badges */}
        <Stack direction="row" spacing={1.5} sx={{ mb: 4, flexWrap: 'wrap', gap: 1 }}>
          <Box sx={{
            display: 'inline-flex',
            alignItems: 'center',
            bgcolor: alpha(theme.palette.primary.light, 0.12),
            border: '1px solid',
            borderColor: alpha(theme.palette.primary.light, 0.25),
            borderRadius: '30px',
            px: 1.75,
            py: 0.5,
            color: 'primary.light',
            fontWeight: 600,
            fontSize: '0.75rem'
          }}>
            <CheckCircleIcon sx={{ fontSize: 13, mr: 0.75 }} />
            WCAG 2.2 Compliance
          </Box>
          <Box sx={{
            display: 'inline-flex',
            alignItems: 'center',
            bgcolor: alpha(theme.palette.primary.light, 0.12),
            border: '1px solid',
            borderColor: alpha(theme.palette.primary.light, 0.25),
            borderRadius: '30px',
            px: 1.75,
            py: 0.5,
            color: 'primary.light',
            fontWeight: 600,
            fontSize: '0.75rem'
          }}>
            <CheckCircleIcon sx={{ fontSize: 13, mr: 0.75 }} />
            Real-time Remediation
          </Box>
        </Stack>
      </Box>

      {/* Premium Dashboard Visualization mockup */}
      <Box sx={{
        width: '100%',
        display: { xs: 'none', md: 'block' },
        mt: 'auto',
        zIndex: 1,
        position: 'relative',
        overflow: 'hidden',
        maxHeight: '40vh'
      }}>
        <Box 
          component="img" 
          src="/assets/img/dashboard_mockup.png" 
          alt="A11ySense AI Dashboard Preview" 
          sx={{
            width: '100%',
            height: 'auto',
            maxHeight: '35vh',
            objectFit: 'contain',
            borderRadius: '8px',
            border: '1px solid',
            borderColor: alpha(theme.palette.common.white, 0.15),
            boxShadow: `0 20px 40px ${alpha(theme.palette.common.black, 0.5)}`,
            background: 'text.primary',
            transform: 'perspective(1200px) rotateY(-8deg) rotateX(4deg)',
            transformOrigin: 'right center',
            transition: 'transform 0.4s cubic-bezier(0.16, 1, 0.3, 1)',
            '&:hover': {
              transform: 'perspective(1200px) rotateY(0deg) rotateX(0deg)'
            }
          }} 
        />
      </Box>
    </Box>
  );
};

export default ShowcasePanel;
