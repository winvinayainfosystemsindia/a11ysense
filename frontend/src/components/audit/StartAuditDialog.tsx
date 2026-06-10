import React, { useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  MenuItem,
  Stack,
  CircularProgress,
  Typography,
  Alert
} from '@mui/material';
import { Button } from '../common/button';
import { useAppDispatch } from '../../store';
import { initiateAudit, clearAuditTask } from '../../store/slices/auditSlice';
import { fetchDashboardStats } from '../../store/slices/dashboardSlice';

interface StartAuditDialogProps {
  open: boolean;
  onClose: () => void;
  onSuccess?: () => void;
}

export const StartAuditDialog: React.FC<StartAuditDialogProps> = ({ open, onClose, onSuccess }) => {
  const [url, setUrl] = useState('');
  const [depth, setDepth] = useState(2);
  const [loading, setLoading] = useState(false);
  
  const dispatch = useAppDispatch();
  const userRole = localStorage.getItem('user_role') || 'Viewer';
  const isViewer = userRole.toLowerCase() === 'viewer';

  const handleStartAudit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!url) return;
    
    setLoading(true);
    dispatch(clearAuditTask());

    try {
      await dispatch(initiateAudit({ request: { url, depth } })).unwrap();
      // On success, refresh the dashboard to show the new audit in the table
      await dispatch(fetchDashboardStats());
      
      if (onSuccess) {
        onSuccess();
      }

      // Close the dialog and reset form
      handleClose();
    } catch (err: any) {
      console.error(err);
      // errors handled by toastMiddleware
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    if (!loading) {
      setUrl('');
      setDepth(2);
      onClose();
    }
  };

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="sm" fullWidth>
      <form onSubmit={handleStartAudit}>
        <DialogTitle sx={{ fontWeight: 'bold' }}>Start New Audit</DialogTitle>
        <DialogContent dividers>
          {isViewer && (
            <Alert severity="warning" sx={{ mb: 3, borderRadius: 2, fontWeight: '600' }}>
              You are signed in as a Viewer. Viewer accounts have read-only access and cannot start new audits.
            </Alert>
          )}
          
          <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
            Audit your entire site structure. Discovers pages recursively and runs deep compliance scans.
          </Typography>

          <Stack spacing={3}>
            <TextField
              fullWidth
              label="Starting Site URL"
              variant="outlined"
              placeholder="https://example.com"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              disabled={isViewer || loading}
              required
              type="url"
              autoFocus
            />
            
            <TextField
              select
              fullWidth
              label="Crawl Depth"
              value={depth}
              onChange={(e) => setDepth(Number(e.target.value))}
              disabled={isViewer || loading}
            >
              <MenuItem value={1}>1 (Single Page)</MenuItem>
              <MenuItem value={2}>2 Levels</MenuItem>
              <MenuItem value={3}>3 Levels</MenuItem>
              <MenuItem value={4}>4 Levels</MenuItem>
              <MenuItem value={5}>5 Levels</MenuItem>
            </TextField>
          </Stack>
        </DialogContent>
        <DialogActions sx={{ p: 2, px: 3 }}>
          <Button onClick={handleClose} disabled={loading} variant="text" color="inherit">
            Cancel
          </Button>
          <Button
            type="submit"
            variant="contained"
            disabled={isViewer || loading || !url}
            startIcon={loading ? <CircularProgress size={20} color="inherit" /> : null}
          >
            {loading ? 'Triggering System...' : 'Start Audit'}
          </Button>
        </DialogActions>
      </form>
    </Dialog>
  );
};
