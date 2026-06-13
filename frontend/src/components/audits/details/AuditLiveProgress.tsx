import React from 'react';
import { Box, Card, Stack, Typography, LinearProgress, Grid, Divider, List, ListItem, ListItemIcon, ListItemText, CircularProgress } from '@mui/material';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import type { AuditTaskDetail } from '../../../service/auditService';

interface AuditLiveProgressProps {
  taskDetail: AuditTaskDetail;
}

export const AuditLiveProgress: React.FC<AuditLiveProgressProps> = ({ taskDetail }) => {
  return (
    <Card variant="outlined" sx={{ p: 4, borderRadius: '16px', mb: 4 }}>
      <Stack component="div" spacing={3}>
        <Box>
          <Stack component="div" direction="row" sx={{ justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
            <Typography variant="h5" sx={{ fontWeight: '700' }}>
              {taskDetail.status === 'crawling' ? 'Site Crawl in Progress...' : 'Evaluating Accessibility Rules...'}
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ fontWeight: '600' }}>
              {taskDetail.pages_completed} / {taskDetail.pages_total} Pages Audited
            </Typography>
          </Stack>
          <LinearProgress 
            variant="determinate" 
            value={taskDetail.pages_total ? (taskDetail.pages_completed! / taskDetail.pages_total!) * 100 : 0} 
            sx={{ height: 8, borderRadius: 4, bgcolor: '#e2e8f0', '& .MuiLinearProgress-bar': { borderRadius: 4 } }}
          />
        </Box>

        <Grid container spacing={3}>
          <Grid size={{ xs: 12, md: 4 }}>
            <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 0.5, fontWeight: '700' }}>PAGES DISCOVERED</Typography>
            <Typography variant="h4" sx={{ fontWeight: '800' }}>{taskDetail.pages_found}</Typography>
          </Grid>
          <Grid size={{ xs: 12, md: 4 }}>
            <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 0.5, fontWeight: '700' }}>AUDITED PAGES</Typography>
            <Typography variant="h4" sx={{ fontWeight: '800', color: 'success.main' }}>{taskDetail.pages_completed}</Typography>
          </Grid>
          <Grid size={{ xs: 12, md: 4 }}>
            <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 0.5, fontWeight: '700' }}>PENDING PAGES</Typography>
            <Typography variant="h4" sx={{ fontWeight: '800', color: 'warning.main' }}>{(taskDetail.pages_total || 0) - (taskDetail.pages_completed || 0)}</Typography>
          </Grid>
        </Grid>

        <Divider />

        <Box>
          <Typography variant="subtitle2" sx={{ fontWeight: '700', mb: 1.5 }}>Crawled Pages Queue</Typography>
          <Box sx={{ maxHeight: 200, overflowY: 'auto', border: '1px solid #e2e8f0', borderRadius: '8px', bgcolor: '#f8fafc' }}>
            <List dense>
              {taskDetail.pages_discovered?.map((url: string, index: number) => {
                const isScanned = taskDetail.pages_scanned?.includes(url);
                return (
                  <ListItem key={index}>
                    <ListItemIcon sx={{ minWidth: 32 }}>
                      {isScanned ? (
                        <CheckCircleIcon fontSize="small" color="success" sx={{ fontSize: '1.1rem' }} />
                      ) : (
                        <CircularProgress size={12} thickness={5} />
                      )}
                    </ListItemIcon>
                    <ListItemText 
                      primary={
                        <Typography sx={{ fontFamily: 'monospace', fontSize: '0.75rem', color: isScanned ? 'text.primary' : 'text.secondary', fontWeight: isScanned ? '400' : '600' }}>
                          {url}
                        </Typography>
                      }
                    />
                  </ListItem>
                );
              })}
              {!taskDetail.pages_discovered?.length && (
                <ListItem>
                  <ListItemText 
                    primary={
                      <Typography sx={{ fontSize: '0.875rem', color: 'text.secondary', fontStyle: 'italic' }}>
                        Discovering site pages...
                      </Typography>
                    } 
                  />
                </ListItem>
              )}
            </List>
          </Box>
        </Box>
      </Stack>
    </Card>
  );
};
