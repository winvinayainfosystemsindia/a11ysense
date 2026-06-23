import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  Dialog,
  TextField,
  MenuItem,
  Stack,
  Typography,
  Alert,
  ToggleButtonGroup,
  ToggleButton,
  Box,
  List,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Checkbox,
  CircularProgress,
  Chip,
} from '@mui/material';
import { Button } from '../common/button';
import { EnterpriseForm, type FormStep } from '../common/form';
import { useAppDispatch, useAppSelector } from '../../store';
import { initiateAudit, clearAuditTask } from '../../store/slices/auditSlice';
import { initiateCrawlDiscovery, fetchCrawlDiscoveryStatus, clearCrawlTask } from '../../store/slices/crawlDiscoverySlice';
import { fetchDashboardStats } from '../../store/slices/dashboardSlice';
import { fetchProjects, createNewProject } from '../../store/slices/projectSlice';
import { credentialService } from '../../service/credentialService';
import type { Credential } from '../../service/credentialService';
import type { ScanTarget } from '../../model/audit.model';

interface StartAuditWizardProps {
  open: boolean;
  onClose: () => void;
  onSuccess?: () => void;
}

const SCAN_TARGET_OPTIONS: { value: ScanTarget; label: string; description: string }[] = [
  { value: 'web_page', label: 'Web Page', description: 'Public pages, no login required' },
  { value: 'web_application', label: 'Web Application', description: 'Requires login credentials' },
  { value: 'both', label: 'Both', description: 'Combine public and authenticated pages' },
];

const POLL_INTERVAL_MS = 2500;

export const StartAuditWizard: React.FC<StartAuditWizardProps> = ({ open, onClose, onSuccess }) => {
  const dispatch = useAppDispatch();
  const userRole = localStorage.getItem('user_role') || 'Viewer';
  const isViewer = userRole.toLowerCase() === 'viewer';

  const projects = useAppSelector((state) => state.project.projects);
  const projectsLoading = useAppSelector((state) => state.project.loading);
  const currentCrawlTask = useAppSelector((state) => state.crawlDiscovery.currentCrawlTask);
  const crawlLoading = useAppSelector((state) => state.crawlDiscovery.loading);
  const crawlError = useAppSelector((state) => state.crawlDiscovery.error);

  const [activeStep, setActiveStep] = useState(0);
  const [selectedProjectId, setSelectedProjectId] = useState('');
  const [newProjectName, setNewProjectName] = useState('');
  const [creatingProject, setCreatingProject] = useState(false);
  const [scanTarget, setScanTarget] = useState<ScanTarget>('web_page');
  const [url, setUrl] = useState('');
  const [credentialsList, setCredentialsList] = useState<Credential[]>([]);
  const [credentialsId, setCredentialsId] = useState('');
  const [selectedUrls, setSelectedUrls] = useState<string[]>([]);
  const [submitting, setSubmitting] = useState(false);

  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const requiresCredentials = scanTarget !== 'web_page';

  // Effective project: whatever the user explicitly picked, falling back to
  // their first project until they pick one. Derived at render time instead
  // of synced into state via an effect.
  const effectiveProjectId = selectedProjectId || projects[0]?.id || '';

  useEffect(() => {
    if (open && projects.length === 0) {
      dispatch(fetchProjects());
    }
  }, [open, projects, dispatch]);

  useEffect(() => {
    const loadCreds = async () => {
      if (effectiveProjectId) {
        try {
          const creds = await credentialService.getCredentials(effectiveProjectId);
          setCredentialsList(creds);
        } catch (err) {
          console.error('Failed to load credentials for wizard selection:', err);
        }
      }
    };
    if (open && effectiveProjectId) {
      loadCreds();
    }
  }, [open, effectiveProjectId]);

  // Poll the crawl-discovery task until it settles, then default all
  // discovered pages to selected (pre-checked) the moment it completes.
  useEffect(() => {
    const isActive = currentCrawlTask && (currentCrawlTask.status === 'queued' || currentCrawlTask.status === 'crawling');
    if (!isActive) {
      return;
    }
    const crawlTaskId = currentCrawlTask.crawl_task_id;
    pollRef.current = setInterval(() => {
      dispatch(fetchCrawlDiscoveryStatus(crawlTaskId))
        .unwrap()
        .then((task) => {
          if (task.status === 'completed') {
            setSelectedUrls(task.pages_discovered || []);
          }
        })
        .catch(() => {});
    }, POLL_INTERVAL_MS);
    return () => {
      if (pollRef.current) {
        clearInterval(pollRef.current);
        pollRef.current = null;
      }
    };
  }, [currentCrawlTask?.status, currentCrawlTask?.crawl_task_id, dispatch]);

  const handleCreateProject = async () => {
    if (!newProjectName.trim()) return;
    setCreatingProject(true);
    try {
      const project = await dispatch(createNewProject(newProjectName.trim())).unwrap();
      setSelectedProjectId(project.id);
      setNewProjectName('');
    } catch (err) {
      console.error('Failed to create project:', err);
    } finally {
      setCreatingProject(false);
    }
  };

  const handleStartDiscovery = () => {
    if (!url) return;
    dispatch(
      initiateCrawlDiscovery({
        request: {
          url,
          scan_target: scanTarget,
          credentials_id: requiresCredentials && credentialsId ? credentialsId : undefined,
        },
        projectId: effectiveProjectId,
      })
    )
      .unwrap()
      .then((task) => {
        // Covers the (unlikely) case where discovery finishes before the polling effect attaches.
        if (task.status === 'completed') {
          setSelectedUrls(task.pages_discovered || []);
        }
      })
      .catch(() => {});
  };

  const toggleUrl = (pageUrl: string) => {
    setSelectedUrls((prev) =>
      prev.includes(pageUrl) ? prev.filter((u) => u !== pageUrl) : [...prev, pageUrl]
    );
  };

  const handleSelectAllToggle = () => {
    const allPages = currentCrawlTask?.pages_discovered || [];
    setSelectedUrls((prev) => (prev.length === allPages.length ? [] : allPages));
  };

  const handleStartAudit = async () => {
    if (!url || selectedUrls.length === 0) return;
    setSubmitting(true);
    dispatch(clearAuditTask());

    try {
      await dispatch(
        initiateAudit({
          request: {
            url,
            audit_type: scanTarget,
            credentials_id: requiresCredentials && credentialsId ? credentialsId : undefined,
            selected_urls: selectedUrls,
            crawl_task_id: currentCrawlTask?.crawl_task_id,
          },
          projectId: effectiveProjectId || undefined,
        })
      ).unwrap();
      await dispatch(fetchDashboardStats());

      if (onSuccess) {
        onSuccess();
      }
      handleClose();
    } catch (err: any) {
      console.error(err);
      // errors handled by toastMiddleware
    } finally {
      setSubmitting(false);
    }
  };

  const handleClose = () => {
    if (submitting) return;
    setScanTarget('web_page');
    setUrl('');
    setCredentialsId('');
    setSelectedUrls([]);
    setNewProjectName('');
    setActiveStep(0);
    dispatch(clearCrawlTask());
    onClose();
  };

  const handleStepChange = useCallback((step: number) => setActiveStep(step), []);

  const allSelected = currentCrawlTask?.pages_discovered?.length === selectedUrls.length && selectedUrls.length > 0;
  const discoveryCompleted = currentCrawlTask?.status === 'completed';
  const discoveryRunning = currentCrawlTask?.status === 'queued' || currentCrawlTask?.status === 'crawling';
  const discoveryFailed = currentCrawlTask?.status === 'failed';

  const nextDisabled =
    activeStep === 0
      ? isViewer || !effectiveProjectId || !url.trim() || (requiresCredentials && !credentialsId)
      : activeStep === 1
      ? !discoveryCompleted || selectedUrls.length === 0
      : false;

  const steps: FormStep[] = [
    {
      label: 'Configure',
      description: 'Audit type, URL & credentials',
      content: (
        <Stack spacing={3}>
          {isViewer && (
            <Alert severity="warning" sx={{ borderRadius: 2, fontWeight: 600 }}>
              You are signed in as a Viewer. Viewer accounts have read-only access and cannot start new audits.
            </Alert>
          )}

          <Box>
            <Typography variant="subtitle2" sx={{ fontWeight: 700, mb: 1.5 }}>
              Project
            </Typography>
            {projectsLoading && projects.length === 0 ? (
              <Stack component="div" direction="row" spacing={1.5} sx={{ alignItems: 'center' }}>
                <CircularProgress size={18} />
                <Typography variant="body2" color="text.secondary">Loading projects...</Typography>
              </Stack>
            ) : projects.length === 0 ? (
              <Stack spacing={1.5}>
                <Alert severity="info" sx={{ borderRadius: 2 }}>
                  You don't have any projects yet. Create one to start an audit.
                </Alert>
                <Stack component="div" direction="row" spacing={1.5}>
                  <TextField
                    fullWidth
                    size="small"
                    label="New Project Name"
                    value={newProjectName}
                    onChange={(e) => setNewProjectName(e.target.value)}
                    disabled={isViewer || creatingProject}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') handleCreateProject();
                    }}
                  />
                  <Button
                    variant="contained"
                    onClick={handleCreateProject}
                    disabled={isViewer || creatingProject || !newProjectName.trim()}
                  >
                    {creatingProject ? 'Creating...' : 'Create'}
                  </Button>
                </Stack>
              </Stack>
            ) : (
              <TextField
                select
                fullWidth
                value={effectiveProjectId}
                onChange={(e) => setSelectedProjectId(e.target.value)}
                disabled={isViewer}
              >
                {projects.map((p) => (
                  <MenuItem key={p.id} value={p.id}>{p.name}</MenuItem>
                ))}
              </TextField>
            )}
          </Box>

          <Box>
            <Typography variant="subtitle2" sx={{ fontWeight: 700, mb: 1.5 }}>
              What do you want to audit?
            </Typography>
            <ToggleButtonGroup
              value={scanTarget}
              exclusive
              onChange={(_e, value) => value && setScanTarget(value)}
              disabled={isViewer}
              fullWidth
            >
              {SCAN_TARGET_OPTIONS.map((opt) => (
                <ToggleButton key={opt.value} value={opt.value} sx={{ flexDirection: 'column', py: 1.5, textTransform: 'none' }}>
                  <Typography variant="body2" sx={{ fontWeight: 700 }}>{opt.label}</Typography>
                  <Typography variant="caption" color="text.secondary">{opt.description}</Typography>
                </ToggleButton>
              ))}
            </ToggleButtonGroup>
          </Box>

          <TextField
            fullWidth
            label="Starting Site URL"
            variant="outlined"
            placeholder="https://example.com"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            disabled={isViewer}
            required
            type="url"
            autoFocus
          />

          {requiresCredentials && (
            <TextField
              select
              fullWidth
              label="Login Credentials"
              value={credentialsId}
              onChange={(e) => setCredentialsId(e.target.value)}
              disabled={isViewer}
              required
              helperText="Required to crawl and audit authenticated pages"
            >
              <MenuItem value="">
                <em>Select credentials...</em>
              </MenuItem>
              {credentialsList.map((c) => (
                <MenuItem key={c.id} value={c.id}>
                  {c.label} ({c.auth_type.toUpperCase()} - {c.login_url})
                </MenuItem>
              ))}
            </TextField>
          )}
        </Stack>
      ),
    },
    {
      label: 'Discover & Select',
      description: 'Pick pages to audit',
      content: (
        <Stack spacing={3}>
          {!currentCrawlTask && (
            <Box sx={{ textAlign: 'center', py: 4 }}>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                Discover every page on the site before choosing which ones to audit.
              </Typography>
              <Button variant="contained" onClick={handleStartDiscovery} disabled={crawlLoading}>
                {crawlLoading ? 'Starting...' : 'Start Discovery'}
              </Button>
            </Box>
          )}

          {discoveryRunning && (
            <Box sx={{ textAlign: 'center', py: 4 }}>
              <CircularProgress size={28} sx={{ mb: 2 }} />
              <Typography variant="body2" color="text.secondary">
                Discovering pages on {url}... this can take a while for large or authenticated sites.
              </Typography>
            </Box>
          )}

          {discoveryFailed && (
            <Alert severity="error">
              {currentCrawlTask?.error || crawlError || 'Page discovery failed.'}
              <Box sx={{ mt: 1.5 }}>
                <Button variant="outlined" onClick={handleStartDiscovery}>Retry Discovery</Button>
              </Box>
            </Alert>
          )}

          {discoveryCompleted && (
            <>
              <Stack component="div" direction="row" sx={{ justifyContent: 'space-between', alignItems: 'center' }}>
                <Typography variant="subtitle2" sx={{ fontWeight: 700 }}>
                  {currentCrawlTask?.pages_discovered?.length || 0} pages discovered
                </Typography>
                <Button variant="text" onClick={handleSelectAllToggle}>
                  {allSelected ? 'Deselect All' : 'Select All'}
                </Button>
              </Stack>
              <List sx={{ maxHeight: 320, overflowY: 'auto', border: '1px solid', borderColor: 'divider', borderRadius: 1 }}>
                {(currentCrawlTask?.pages_discovered || []).map((pageUrl) => (
                  <ListItemButton key={pageUrl} onClick={() => toggleUrl(pageUrl)} dense>
                    <ListItemIcon sx={{ minWidth: 36 }}>
                      <Checkbox edge="start" checked={selectedUrls.includes(pageUrl)} tabIndex={-1} disableRipple />
                    </ListItemIcon>
                    <ListItemText primary={pageUrl} slotProps={{ primary: { sx: { wordBreak: 'break-all', fontSize: '0.85rem' } } }} />
                  </ListItemButton>
                ))}
              </List>
            </>
          )}
        </Stack>
      ),
    },
    {
      label: 'Confirm & Start',
      description: 'Review and launch',
      content: (
        <Stack spacing={2}>
          <Typography variant="subtitle2" sx={{ fontWeight: 700 }}>Audit Summary</Typography>
          <Typography variant="body2" color="text.secondary">
            Project: {projects.find((p) => p.id === effectiveProjectId)?.name || '—'}
          </Typography>
          <Stack component="div" direction="row" spacing={1} sx={{ alignItems: 'center' }}>
            <Chip label={SCAN_TARGET_OPTIONS.find((o) => o.value === scanTarget)?.label} color="primary" size="small" />
            <Typography variant="body2" color="text.secondary">{url}</Typography>
          </Stack>
          {requiresCredentials && credentialsId && (
            <Typography variant="body2" color="text.secondary">
              Credentials: {credentialsList.find((c) => c.id === credentialsId)?.label || credentialsId}
            </Typography>
          )}
          <Typography variant="body2" color="text.secondary">
            {selectedUrls.length} of {currentCrawlTask?.pages_discovered?.length || 0} discovered pages selected for audit.
          </Typography>
          <List sx={{ maxHeight: 240, overflowY: 'auto', border: '1px solid', borderColor: 'divider', borderRadius: 1 }}>
            {selectedUrls.map((pageUrl) => (
              <ListItemText
                key={pageUrl}
                sx={{ px: 2, py: 0.5 }}
                primary={pageUrl}
                slotProps={{ primary: { sx: { wordBreak: 'break-all', fontSize: '0.8rem' } } }}
              />
            ))}
          </List>
        </Stack>
      ),
    },
  ];

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="md" fullWidth slotProps={{ paper: { sx: { bgcolor: 'transparent', boxShadow: 'none' } } }}>
      <EnterpriseForm
        title="Start New Audit"
        mode="create"
        steps={steps}
        onSave={handleStartAudit}
        onCancel={handleClose}
        isSubmitting={submitting}
        saveButtonText="Start Audit"
        nextDisabled={nextDisabled}
        saveDisabled={isViewer || submitting || selectedUrls.length === 0}
        onStepChange={handleStepChange}
      />
    </Dialog>
  );
};
