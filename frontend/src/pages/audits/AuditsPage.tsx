import React, { useState, useEffect } from 'react';
import { Box, Typography, Stack, Button, IconButton } from '@mui/material';
import RefreshIcon from '@mui/icons-material/Refresh';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import AuditsTable from '../../components/audits/AuditsTable';
import { StartAuditDialog } from '../../components/audit/StartAuditDialog';
import { auditService } from '../../service/auditService';
import type { AuditSessionInfo } from '../../service/auditService';

const AuditsPage: React.FC = () => {
  const [audits, setAudits] = useState<AuditSessionInfo[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isDialogOpen, setIsDialogOpen] = useState(false);

  const fetchAudits = async () => {
    setIsLoading(true);
    try {
      const data = await auditService.getAudits();
      setAudits(data);
    } catch (err) {
      console.error('Failed to fetch audits:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchAudits();
    
    // Set up auto-refresh every 15 seconds to update progress
    const interval = setInterval(() => {
      fetchAudits();
    }, 15000);
    
    return () => clearInterval(interval);
  }, []);

  const handleAuditStarted = () => {
    setIsDialogOpen(false);
    // Immediately fetch to show the new 'in_progress' audit
    fetchAudits();
  };

  return (
    <Box sx={{ pb: 4 }}>
      <Stack component="div" direction="row" sx={{ justifyContent: 'space-between', alignItems: 'center', mb: 4 }}>
        <Box>
          <Typography variant="h4" sx={{ fontWeight: '800', mb: 0.5, letterSpacing: '-0.5px' }}>
            Audit History
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Track ongoing scans and review past accessibility reports.
          </Typography>
        </Box>
        
        <Stack component="div" direction="row" spacing={2} sx={{ alignItems: 'center' }}>
          <IconButton onClick={fetchAudits} color="primary" sx={{ bgcolor: 'background.paper', boxShadow: 1 }} title="Refresh">
            <RefreshIcon />
          </IconButton>
          
          <Button
            variant="contained"
            color="primary"
            startIcon={<PlayArrowIcon />}
            onClick={() => setIsDialogOpen(true)}
            sx={{ fontWeight: '700', borderRadius: '8px', px: 3 }}
          >
            New Audit
          </Button>
        </Stack>
      </Stack>

      <AuditsTable audits={audits} isLoading={isLoading} onRefresh={fetchAudits} />

      <StartAuditDialog 
        open={isDialogOpen} 
        onClose={() => setIsDialogOpen(false)} 
        onSuccess={handleAuditStarted}
      />
    </Box>
  );
};

export default AuditsPage;
