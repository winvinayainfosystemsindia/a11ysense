import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Stack,
  Button,
  IconButton,
  CircularProgress,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  MenuItem,
  FormControl,
  InputLabel,
  Select,
  Alert,
  Snackbar,
  Card,
  CardContent,
  Grid,
} from '@mui/material';
import DeleteIcon from '@mui/icons-material/Delete';
import EditIcon from '@mui/icons-material/Edit';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import LockIcon from '@mui/icons-material/Lock';
import AddIcon from '@mui/icons-material/Add';

import { useAppDispatch, useAppSelector } from '../../store';
import { fetchProjects } from '../../store/slices/projectSlice';
import { credentialService } from '../../service/credentialService';
import type { Credential, CredentialCreate } from '../../service/credentialService';

const CredentialsPage: React.FC = () => {
  const dispatch = useAppDispatch();
  const { projects, loading: projectsLoading } = useAppSelector((state) => state.project);
  
  const [selectedProjectId, setSelectedProjectId] = useState<string>('');
  const [credentials, setCredentials] = useState<Credential[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  
  // Dialog State
  const [isOpen, setIsOpen] = useState(false);
  const [editMode, setEditMode] = useState(false);
  const [selectedCredId, setSelectedCredId] = useState<string | null>(null);
  
  // Form Fields
  const [label, setLabel] = useState('');
  const [loginUrl, setLoginUrl] = useState('');
  const [urlPattern, setUrlPattern] = useState('');
  const [authType, setAuthType] = useState('form');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [usernameField, setUsernameField] = useState('[name=username]');
  const [passwordField, setPasswordField] = useState('[name=password]');
  const [submitSelector, setSubmitSelector] = useState('button[type=submit]');
  const [postLoginUrlPattern, setPostLoginUrlPattern] = useState('');
  const [extraFieldsText, setExtraFieldsText] = useState('');

  // Status indicators
  const [testingId, setTestingId] = useState<string | null>(null);
  const [snackbarMessage, setSnackbarMessage] = useState('');
  const [snackbarSeverity, setSnackbarSeverity] = useState<'success' | 'error' | 'warning' | 'info'>('success');

  const userRole = localStorage.getItem('user_role') || 'Viewer';
  const isViewer = userRole.toLowerCase() === 'viewer';

  // Load projects on mount
  useEffect(() => {
    dispatch(fetchProjects());
  }, [dispatch]);

  // Set default project ID when projects list loads
  useEffect(() => {
    if (projects.length > 0 && !selectedProjectId) {
      setSelectedProjectId(projects[0].id);
    }
  }, [projects, selectedProjectId]);

  // Load credentials when selected project changes
  useEffect(() => {
    if (selectedProjectId) {
      loadCredentials(selectedProjectId);
    }
  }, [selectedProjectId]);

  const loadCredentials = async (projId: string) => {
    setIsLoading(true);
    try {
      const data = await credentialService.getCredentials(projId);
      setCredentials(data);
    } catch (err) {
      console.error('Failed to load credentials:', err);
      showToast('Error: Failed to retrieve project credentials.', 'error');
    } finally {
      setIsLoading(false);
    }
  };

  const showToast = (msg: string, severity: 'success' | 'error' | 'warning' | 'info' = 'success') => {
    setSnackbarMessage(msg);
    setSnackbarSeverity(severity);
  };

  const handleOpenDialog = (cred?: Credential) => {
    if (cred) {
      setEditMode(true);
      setSelectedCredId(cred.id);
      setLabel(cred.label);
      setLoginUrl(cred.login_url);
      setUrlPattern(cred.url_pattern);
      setAuthType(cred.auth_type);
      setUsername(''); // Password and username inputs start empty on edit for security
      setPassword('');
      setUsernameField(cred.username_field || '[name=username]');
      setPasswordField(cred.password_field || '[name=password]');
      setSubmitSelector(cred.submit_selector || 'button[type=submit]');
      setPostLoginUrlPattern(cred.post_login_url_pattern || '');
      // Extra fields handling
      setExtraFieldsText('');
    } else {
      setEditMode(false);
      setSelectedCredId(null);
      setLabel('');
      setLoginUrl('');
      setUrlPattern('*');
      setAuthType('form');
      setUsername('');
      setPassword('');
      setUsernameField('[name=username]');
      setPasswordField('[name=password]');
      setSubmitSelector('button[type=submit]');
      setPostLoginUrlPattern('');
      setExtraFieldsText('');
    }
    setIsOpen(true);
  };

  const handleCloseDialog = () => {
    setIsOpen(false);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedProjectId) return;

    let extraFields: Record<string, string> | undefined = undefined;
    if (extraFieldsText.trim()) {
      try {
        extraFields = JSON.parse(extraFieldsText.trim());
      } catch (err) {
        showToast('Error: Invalid JSON format in extra fields.', 'error');
        return;
      }
    }

    const payload: CredentialCreate = {
      label,
      login_url: loginUrl,
      url_pattern: urlPattern,
      auth_type: authType,
      username: username || undefined,
      password: password || undefined,
      username_field: usernameField || undefined,
      password_field: passwordField || undefined,
      submit_selector: submitSelector || undefined,
      post_login_url_pattern: postLoginUrlPattern || undefined,
      extra_fields: extraFields,
    };

    try {
      if (editMode && selectedCredId) {
        await credentialService.updateCredential(selectedProjectId, selectedCredId, payload);
        showToast('Credential configuration updated successfully.');
      } else {
        await credentialService.createCredential(selectedProjectId, payload);
        showToast('New credential configuration created successfully.');
      }
      loadCredentials(selectedProjectId);
      handleCloseDialog();
    } catch (err: any) {
      console.error(err);
      showToast(err.response?.data?.detail || 'Failed to save credential configuration.', 'error');
    }
  };

  const handleDelete = async (credId: string) => {
    if (!window.confirm('Are you sure you want to delete this credential configuration?')) return;
    try {
      await credentialService.deleteCredential(selectedProjectId, credId);
      showToast('Credential configuration deleted successfully.');
      loadCredentials(selectedProjectId);
    } catch (err) {
      console.error(err);
      showToast('Failed to delete credential configuration.', 'error');
    }
  };

  const handleTestLogin = async (credId: string) => {
    setTestingId(credId);
    showToast('Triggering verification test login. Please wait...', 'info');
    try {
      const res = await credentialService.testCredential(selectedProjectId, credId);
      if (res.status === 'success') {
        showToast(`Verification Successful! Target page authentication verified successfully. (${res.cookies_count} cookies generated)`, 'success');
      } else {
        showToast(`Verification Failed: ${res.message || 'Check credentials.'}`, 'error');
      }
    } catch (err: any) {
      console.error(err);
      const detail = err.response?.data?.detail || err.message || 'Verification failed.';
      showToast(`Verification Failed: ${detail}`, 'error');
    } finally {
      setTestingId(null);
    }
  };

  return (
    <Box sx={{ pb: 4 }}>
      {/* Header */}
      <Stack component="div" direction="row" sx={{ justifyContent: 'space-between', alignItems: 'center', mb: 4 }}>
        <Box>
          <Typography variant="h4" sx={{ fontWeight: '800', mb: 0.5, letterSpacing: '-0.5px' }}>
            Credential Management
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Store login credentials for auditing protected sections of your web applications.
          </Typography>
        </Box>
        
        {!isViewer && (
          <Button
            variant="contained"
            color="primary"
            startIcon={<AddIcon />}
            onClick={() => handleOpenDialog()}
            sx={{ fontWeight: '700', borderRadius: '8px', px: 3 }}
          >
            Add Credential
          </Button>
        )}
      </Stack>

      {/* Project Selector Card */}
      <Card sx={{ mb: 4, borderRadius: '12px', boxShadow: 1 }}>
        <CardContent sx={{ p: 3 }}>
          <Grid container spacing={3} component="div" sx={{ alignItems: 'center' }}>
            <Grid size={{ xs: 12, md: 6 }} component="div">
              <FormControl fullWidth variant="outlined">
                <InputLabel id="project-selector-label">Target Audit Project</InputLabel>
                <Select
                  labelId="project-selector-label"
                  id="project-selector"
                  value={selectedProjectId}
                  onChange={(e) => setSelectedProjectId(e.target.value)}
                  label="Target Audit Project"
                  disabled={projectsLoading}
                >
                  {projectsLoading ? (
                    <MenuItem value="" disabled><CircularProgress size={20} sx={{ mr: 1 }} /> Loading projects...</MenuItem>
                  ) : (
                    projects.map((p) => (
                      <MenuItem key={p.id} value={p.id}>{p.name}</MenuItem>
                    ))
                  )}
                </Select>
              </FormControl>
            </Grid>
            <Grid size={{ xs: 12, md: 6 }} component="div">
              <Typography variant="body2" color="text.secondary">
                Credentials are bound to specific projects. The crawler uses URL pattern matching to dynamically authenticate when encountering matching paths.
              </Typography>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* Table Section */}
      {isLoading ? (
        <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', py: 8 }}>
          <CircularProgress color="primary" />
          <Typography variant="body2" color="text.secondary" sx={{ mt: 2, fontWeight: '500' }}>
            Fetching project credentials...
          </Typography>
        </Box>
      ) : credentials.length === 0 ? (
        <Paper sx={{ p: 6, textAlign: 'center', borderRadius: '12px' }}>
          <LockIcon sx={{ fontSize: 48, color: 'text.secondary', mb: 2 }} />
          <Typography variant="h6" sx={{ fontWeight: 'bold' }}>No credentials configured</Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
            Add credentials to enable the scanner to log into authentication portals.
          </Typography>
          {!isViewer && (
            <Button variant="outlined" onClick={() => handleOpenDialog()} startIcon={<AddIcon />}>
              Configure Credential
            </Button>
          )}
        </Paper>
      ) : (
        <TableContainer component={Paper} sx={{ borderRadius: '12px', overflow: 'hidden' }}>
          <Table>
            <TableHead sx={{ bgcolor: 'action.hover' }}>
              <TableRow>
                <TableCell sx={{ fontWeight: 'bold' }}>Label</TableCell>
                <TableCell sx={{ fontWeight: 'bold' }}>Login Page URL</TableCell>
                <TableCell sx={{ fontWeight: 'bold' }}>URL Match Pattern</TableCell>
                <TableCell sx={{ fontWeight: 'bold' }}>Auth Method</TableCell>
                <TableCell sx={{ fontWeight: 'bold' }}>Masked User</TableCell>
                <TableCell align="center" sx={{ fontWeight: 'bold' }}>Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {credentials.map((c) => (
                <TableRow key={c.id}>
                  <TableCell sx={{ fontWeight: 'bold' }}>{c.label}</TableCell>
                  <TableCell sx={{ fontFamily: 'monospace', fontSize: '0.82rem' }}>{c.login_url}</TableCell>
                  <TableCell sx={{ fontFamily: 'monospace', fontSize: '0.82rem' }}>{c.url_pattern}</TableCell>
                  <TableCell>
                    <Chip
                      label={c.auth_type.toUpperCase()}
                      size="small"
                      color={c.auth_type === 'form' ? 'primary' : 'secondary'}
                      variant="outlined"
                      sx={{ fontWeight: 'bold' }}
                    />
                  </TableCell>
                  <TableCell>{c.username_masked || '—'}</TableCell>
                  <TableCell align="center">
                    <Stack component="div" direction="row" spacing={1} sx={{ justifyContent: 'center' }}>
                      <Button
                        size="small"
                        variant="outlined"
                        color="success"
                        startIcon={testingId === c.id ? <CircularProgress size={14} color="inherit" /> : <PlayArrowIcon />}
                        onClick={() => handleTestLogin(c.id)}
                        disabled={testingId !== null}
                      >
                        {testingId === c.id ? 'Testing...' : 'Test Login'}
                      </Button>
                      {!isViewer && (
                        <>
                          <IconButton onClick={() => handleOpenDialog(c)} color="info" size="small">
                            <EditIcon fontSize="small" />
                          </IconButton>
                          <IconButton onClick={() => handleDelete(c.id)} color="error" size="small">
                            <DeleteIcon fontSize="small" />
                          </IconButton>
                        </>
                      )}
                    </Stack>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )}

      {/* Create/Edit Dialog */}
      <Dialog open={isOpen} onClose={handleCloseDialog} maxWidth="md" fullWidth>
        <form onSubmit={handleSubmit}>
          <DialogTitle sx={{ fontWeight: 'bold' }}>
            {editMode ? 'Edit Credential Configuration' : 'Configure New Credential'}
          </DialogTitle>
          <DialogContent dividers>
            <Stack component="div" spacing={3}>
              <Grid container spacing={3} component="div">
                <Grid size={{ xs: 12, sm: 6 }} component="div">
                  <TextField
                    fullWidth
                    label="Credential Label"
                    placeholder="e.g. Test Staging Admin"
                    value={label}
                    onChange={(e) => setLabel(e.target.value)}
                    required
                  />
                </Grid>
                <Grid size={{ xs: 12, sm: 6 }} component="div">
                  <FormControl fullWidth>
                    <InputLabel id="auth-type-label">Auth Method</InputLabel>
                    <Select
                      labelId="auth-type-label"
                      value={authType}
                      onChange={(e) => setAuthType(e.target.value)}
                      label="Auth Method"
                    >
                      <MenuItem value="form">Form Based Login</MenuItem>
                      <MenuItem value="cookie">Session Cookies</MenuItem>
                      <MenuItem value="bearer_token">Bearer Token Injection</MenuItem>
                    </Select>
                  </FormControl>
                </Grid>
              </Grid>

              <Grid container spacing={3} component="div">
                <Grid size={{ xs: 12, sm: 6 }} component="div">
                  <TextField
                    fullWidth
                    label="Login URL"
                    placeholder="https://example.com/login"
                    value={loginUrl}
                    onChange={(e) => setLoginUrl(e.target.value)}
                    required
                    type="url"
                  />
                </Grid>
                <Grid size={{ xs: 12, sm: 6 }} component="div">
                  <TextField
                    fullWidth
                    label="URL Scope Pattern (Glob)"
                    placeholder="https://example.com/*"
                    value={urlPattern}
                    onChange={(e) => setUrlPattern(e.target.value)}
                    required
                  />
                </Grid>
              </Grid>

              {authType === 'form' && (
                <>
                  <Grid container spacing={3} component="div">
                    <Grid size={{ xs: 12, sm: 6 }} component="div">
                      <TextField
                        fullWidth
                        label="Username / Email"
                        placeholder="admin@example.com"
                        value={username}
                        onChange={(e) => setUsername(e.target.value)}
                        required={!editMode}
                      />
                    </Grid>
                    <Grid size={{ xs: 12, sm: 6 }} component="div">
                      <TextField
                        fullWidth
                        label="Password"
                        type="password"
                        placeholder={editMode ? "•••••••• (Leave blank to keep unchanged)" : "Password"}
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        required={!editMode}
                      />
                    </Grid>
                  </Grid>

                  <Typography variant="subtitle2" sx={{ fontWeight: 'bold', mt: 2 }}>
                    Form Selectors (Advanced)
                  </Typography>

                  <Grid container spacing={3} component="div">
                    <Grid size={{ xs: 12, sm: 4 }} component="div">
                      <TextField
                        fullWidth
                        label="Username Input Selector"
                        value={usernameField}
                        onChange={(e) => setUsernameField(e.target.value)}
                        helperText="Default: [name=username]"
                      />
                    </Grid>
                    <Grid size={{ xs: 12, sm: 4 }} component="div">
                      <TextField
                        fullWidth
                        label="Password Input Selector"
                        value={passwordField}
                        onChange={(e) => setPasswordField(e.target.value)}
                        helperText="Default: [name=password]"
                      />
                    </Grid>
                    <Grid size={{ xs: 12, sm: 4 }} component="div">
                      <TextField
                        fullWidth
                        label="Submit Button Selector"
                        value={submitSelector}
                        onChange={(e) => setSubmitSelector(e.target.value)}
                        helperText="Default: button[type=submit]"
                      />
                    </Grid>
                  </Grid>

                  <TextField
                    fullWidth
                    label="Successful Redirect URL Match"
                    placeholder="e.g. /dashboard"
                    value={postLoginUrlPattern}
                    onChange={(e) => setPostLoginUrlPattern(e.target.value)}
                    helperText="Ensure crawler validates correct login landing page"
                  />
                </>
              )}

              {authType === 'cookie' && (
                <>
                  <TextField
                    fullWidth
                    label="Username (Cookie Name)"
                    placeholder="session_id"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                  />
                  <TextField
                    fullWidth
                    label="Password (Cookie Value)"
                    placeholder="123456abcdef"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                  />
                  <TextField
                    fullWidth
                    multiline
                    rows={4}
                    label="Alternative Multi-Cookie Payload (JSON)"
                    placeholder='{ "auth_cookie": "xyz", "session_id": "abc" }'
                    value={extraFieldsText}
                    onChange={(e) => setExtraFieldsText(e.target.value)}
                    helperText="Valid JSON string containing cookie keys and values"
                  />
                </>
              )}

              {authType === 'bearer_token' && (
                <>
                  <TextField
                    fullWidth
                    label="Bearer Token Secret"
                    placeholder="eyJhbGciOi..."
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                  />
                </>
              )}
            </Stack>
          </DialogContent>
          <DialogActions sx={{ p: 2, px: 3 }}>
            <Button onClick={handleCloseDialog} variant="text" color="inherit">
              Cancel
            </Button>
            <Button type="submit" variant="contained">
              Save Credential
            </Button>
          </DialogActions>
        </form>
      </Dialog>

      {/* Snackbar notification */}
      <Snackbar
        open={!!snackbarMessage}
        autoHideDuration={6000}
        onClose={() => setSnackbarMessage('')}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert 
          severity={snackbarSeverity} 
          sx={{ width: '100%', borderRadius: '8px', boxShadow: 3 }}
        >
          {snackbarMessage}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default CredentialsPage;
