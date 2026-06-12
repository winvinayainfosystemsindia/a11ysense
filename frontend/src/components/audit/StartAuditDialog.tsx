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
import { useAppDispatch, useAppSelector } from '../../store';
import { initiateAudit, clearAuditTask } from '../../store/slices/auditSlice';
import { fetchDashboardStats } from '../../store/slices/dashboardSlice';
import { fetchProjects } from '../../store/slices/projectSlice';
import { credentialService } from '../../service/credentialService';

interface StartAuditDialogProps {
  open: boolean;
  onClose: () => void;
  onSuccess?: () => void;
}

export const StartAuditDialog: React.FC<StartAuditDialogProps> = ({ open, onClose, onSuccess }) => {
  const [url, setUrl] = useState('');
  const [depth, setDepth] = useState(2);
  const [loading, setLoading] = useState(false);
  const [credentialsList, setCredentialsList] = useState<any[]>([]);
  const [credentialsId, setCredentialsId] = useState<string>('');
  
  const dispatch = useAppDispatch();
  const userRole = localStorage.getItem('user_role') || 'Viewer';
  const isViewer = userRole.toLowerCase() === 'viewer';

  const projects = useAppSelector((state) => state.project.projects);

  React.useEffect(() => {
    if (open) {
      if (projects.length === 0) {
        dispatch(fetchProjects());
      }
    }
  }, [open, projects, dispatch]);

  React.useEffect(() => {
    const loadCreds = async () => {
      const activeProjId = projects[0]?.id;
      if (activeProjId) {
        try {
          const creds = await credentialService.getCredentials(activeProjId);
          setCredentialsList(creds);
        } catch (err) {
          console.error("Failed to load credentials for dialog selection:", err);
        }
      }
    };
    if (open && projects.length > 0) {
      loadCreds();
    }
  }, [open, projects]);

  const handleStartAudit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!url) return;
    
    setLoading(true);
    dispatch(clearAuditTask());

    try {
      const reqPayload: any = { url, depth };
      if (credentialsId) {
        reqPayload.credentials_id = credentialsId;
      }
      await dispatch(initiateAudit({ request: reqPayload })).unwrap();
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
      setCredentialsId('');
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

            <TextField
              select
              fullWidth
              label="Authentication Credentials"
              value={credentialsId}
              onChange={(e) => setCredentialsId(e.target.value)}
              disabled={isViewer || loading}
              helperText="Optional login configurations for scanning protected sections"
            >
              <MenuItem value=""><em>None (Anonymous Scan)</em></MenuItem>
              {credentialsList.map((c) => (
                <MenuItem key={c.id} value={c.id}>
                  {c.label} ({c.auth_type.toUpperCase()} - {c.login_url})
                </MenuItem>
              ))}
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
