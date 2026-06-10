import React from 'react';
import { Card, Stack, Box, Typography, Grid } from '@mui/material';
import { alpha } from '@mui/material/styles';
import type { DashboardStats as StatsType } from '../../model/dashboard.model';

interface CriticalIssuesChartProps {
  stats: StatsType | null;
}

export const CriticalIssuesChart: React.FC<CriticalIssuesChartProps> = ({ stats }) => {

  const critical = stats?.violations_by_impact?.critical || 0;
  const serious = stats?.violations_by_impact?.serious || 0;
  const moderate = stats?.violations_by_impact?.moderate || 0;
  const minor = stats?.violations_by_impact?.minor || 0;

  const maxViolations = Math.max(critical, serious, moderate, minor, 1);
  const criticalHeight = `${(critical / maxViolations) * 100}%`;
  const seriousHeight = `${(serious / maxViolations) * 100}%`;
  const moderateHeight = `${(moderate / maxViolations) * 100}%`;
  const minorHeight = `${(minor / maxViolations) * 100}%`;

  // Dynamic Enterprise Outcomes
  const totalIssues = critical + serious + moderate + minor;
  const complianceRate = totalIssues === 0
    ? 100
    : Math.max(52, Math.round(100 - (critical * 4 + serious * 2 + moderate * 1 + minor * 0.5) / 4));

  // Dynamic POUR Principles calculations
  const perceivableScore = Math.max(55, Math.round(100 - (critical * 3.5 + serious * 1.5) / 3.5));
  const operableScore = Math.max(62, Math.round(100 - (critical * 2.5 + serious * 2) / 3));
  const understandableScore = Math.max(70, Math.round(100 - (serious * 1.5 + moderate * 1) / 2));
  const robustScore = Math.max(78, Math.round(100 - (moderate * 1 + minor * 1.5) / 2));

  const POURData = [
    { name: 'Perceivable', score: perceivableScore, color: '#14b8a6', desc: 'Alt-text, contrast, media' },
    { name: 'Operable', score: operableScore, color: '#0284c7', desc: 'Keyboard access, focus management' },
    { name: 'Understandable', score: understandableScore, color: '#f59e0b', desc: 'Inputs, predictability' },
    { name: 'Robust', score: robustScore, color: '#10b981', desc: 'Markup structure, compatibility' }
  ];

  return (
    <Card variant="outlined" sx={{ p: 3, height: 320, display: 'flex', flexDirection: 'column', bgcolor: 'background.paper' }}>
      {/* Card Title Header */}
      <Stack component="div" direction="row" sx={{ justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="subtitle2" sx={{ fontWeight: '800', color: 'text.secondary', textTransform: 'uppercase', letterSpacing: '0.5px', fontSize: '0.72rem' }}>
          Accessibility Compliance Outlook
        </Typography>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.8 }}>
          <Box sx={{ width: 8, height: 8, bgcolor: 'success.main', borderRadius: '50%' }} />
          <Typography sx={{ fontSize: '0.72rem', fontWeight: '700', color: 'text.secondary' }}>WCAG 2.1 Compliance</Typography>
        </Box>
      </Stack>

      <Grid container spacing={3} sx={{ flexGrow: 1, minHeight: 0 }}>
        {/* Left Side: Vertical Bar Chart */}
        <Grid size={{ xs: 12, sm: 6 }} sx={{ display: 'flex', flexDirection: 'column', height: '100%', borderRight: { sm: '1px solid' }, borderColor: { sm: 'divider' }, pr: { sm: 2.5 } }}>
          <Typography variant="caption" sx={{ color: 'text.disabled', fontWeight: '800', mb: 1.5, fontSize: '0.65rem', letterSpacing: '0.5px', textTransform: 'uppercase' }}>
            Issues by Severity Level
          </Typography>

          <Stack component="div" direction="row" sx={{ justifyContent: 'space-around', alignItems: 'flex-end', flexGrow: 1, pb: 1 }}>
            {/* Level A */}
            <Stack component="div" spacing={1.5} sx={{ alignItems: 'center', justifyContent: 'flex-end', width: 45 }}>
              <Box sx={{ height: 110, width: 12, bgcolor: 'action.hover', borderRadius: '6px', position: 'relative', overflow: 'hidden' }}>
                <Box sx={{ position: 'absolute', bottom: 0, left: 0, right: 0, height: criticalHeight, bgcolor: 'error.main', borderRadius: '0 0 6px 6px' }} />
              </Box>
              <Typography sx={{ fontSize: '0.72rem', fontWeight: '700', color: 'text.secondary', whiteSpace: 'nowrap' }}>Level A ({critical})</Typography>
            </Stack>

            {/* Level AA */}
            <Stack component="div" spacing={1.5} sx={{ alignItems: 'center', justifyContent: 'flex-end', width: 45 }}>
              <Box sx={{ height: 110, width: 12, bgcolor: 'action.hover', borderRadius: '6px', position: 'relative', overflow: 'hidden' }}>
                <Box sx={{ position: 'absolute', bottom: 0, left: 0, right: 0, height: seriousHeight, bgcolor: 'warning.main', borderRadius: '0 0 6px 6px' }} />
              </Box>
              <Typography sx={{ fontSize: '0.72rem', fontWeight: '700', color: 'text.secondary', whiteSpace: 'nowrap' }}>Level AA ({serious})</Typography>
            </Stack>

            {/* Level AAA */}
            <Stack component="div" spacing={1.5} sx={{ alignItems: 'center', justifyContent: 'flex-end', width: 45 }}>
              <Box sx={{ height: 110, width: 12, bgcolor: 'action.hover', borderRadius: '6px', position: 'relative', overflow: 'hidden' }}>
                <Box sx={{ position: 'absolute', bottom: 0, left: 0, right: 0, height: moderateHeight, bgcolor: 'secondary.main', borderRadius: '0 0 6px 6px' }} />
              </Box>
              <Typography sx={{ fontSize: '0.72rem', fontWeight: '700', color: 'text.secondary', whiteSpace: 'nowrap' }}>Level AAA ({moderate})</Typography>
            </Stack>

            {/* BP */}
            <Stack component="div" spacing={1.5} sx={{ alignItems: 'center', justifyContent: 'flex-end', width: 45 }}>
              <Box sx={{ height: 110, width: 12, bgcolor: 'action.hover', borderRadius: '6px', position: 'relative', overflow: 'hidden' }}>
                <Box sx={{ position: 'absolute', bottom: 0, left: 0, right: 0, height: minorHeight, bgcolor: 'primary.main', borderRadius: '0 0 6px 6px' }} />
              </Box>
              <Typography sx={{ fontSize: '0.72rem', fontWeight: '700', color: 'text.secondary', whiteSpace: 'nowrap' }}>BP ({minor})</Typography>
            </Stack>
          </Stack>
        </Grid>

        {/* Right Side: POUR Breakdown / Compliance score */}
        <Grid size={{ xs: 12, sm: 6 }} sx={{ display: 'flex', flexDirection: 'column', height: '100%', pl: { sm: 1.5 } }}>
          <Stack component="div" direction="row" sx={{ justifyContent: 'space-between', alignItems: 'baseline', mb: 2 }}>
            <Typography variant="caption" sx={{ color: 'text.disabled', fontWeight: '800', fontSize: '0.65rem', letterSpacing: '0.5px', textTransform: 'uppercase' }}>
              Compliance Health Score
            </Typography>
            <Stack component="div" direction="row" spacing={0.5} sx={{ alignItems: 'baseline' }}>
              <Typography sx={{ fontSize: '1.25rem', fontWeight: '800', color: complianceRate >= 80 ? 'success.main' : complianceRate >= 65 ? 'warning.main' : 'error.main', lineHeight: 1 }}>
                {complianceRate}%
              </Typography>
              <Typography variant="caption" sx={{ color: 'text.secondary', fontWeight: '700', fontSize: '0.7rem' }}>
                PASS
              </Typography>
            </Stack>
          </Stack>

          {/* POUR Progress Bars */}
          <Stack component="div" spacing={1.5} sx={{ flexGrow: 1, justifyContent: 'center' }}>
            {POURData.map((pour) => (
              <Box key={pour.name}>
                <Stack component="div" direction="row" sx={{ justifyContent: 'space-between', alignItems: 'center', mb: 0.25 }}>
                  <Typography sx={{ fontSize: '0.75rem', fontWeight: '700', color: 'text.primary' }}>
                    {pour.name}
                  </Typography>
                  <Typography sx={{ fontSize: '0.72rem', fontWeight: '800', color: pour.color }}>
                    {pour.score}%
                  </Typography>
                </Stack>
                
                <Box sx={{ position: 'relative', width: '100%', height: 6, bgcolor: alpha(pour.color, 0.1), borderRadius: 3 }}>
                  <Box
                    sx={{
                      position: 'absolute',
                      top: 0,
                      left: 0,
                      height: '100%',
                      width: `${pour.score}%`,
                      bgcolor: pour.color,
                      borderRadius: 3,
                      transition: 'width 0.8s ease-in-out'
                    }}
                  />
                </Box>
              </Box>
            ))}
          </Stack>
        </Grid>
      </Grid>
    </Card>
  );
};
