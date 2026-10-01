import React, { useState, useEffect, useMemo } from 'react';
import {
  Box,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Button,
  TableRow,
  TableCell,
  Snackbar,
  Alert,
  Typography,
  CircularProgress,
  LinearProgress,
  Stack,
  FormControl,
  FormLabel,
  RadioGroup,
  FormControlLabel,
  Radio,
  Chip,
  Paper
} from '@mui/material';
import LanguageIcon from '@mui/icons-material/Language';
import AppShortcutIcon from '@mui/icons-material/AppShortcut';
import DataTable, { type ColumnDefinition } from '../../components/common/table/DataTable';
import { useAppDispatch, useAppSelector } from '../../store';
import { fetchProjects, createNewProject } from '../../store/slices/projectSlice';
import type { ProjectResponse } from '../../model/project.model';

const ProjectsPage: React.FC = () => {
  const dispatch = useAppDispatch();
  const projects = useAppSelector((state) => state.project.projects);
  const loading = useAppSelector((state) => state.project.loading);

  const [snackbarMessage, setSnackbarMessage] = useState('');
  const [searchVal, setSearchVal] = useState('');
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  
  // Form State
  const [name, setName] = useState('');
  const [projectType, setProjectType] = useState<'web_page' | 'web_application'>('web_page');
  const [baseUrl, setBaseUrl] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);

  const userRole = localStorage.getItem('user_role') || 'Viewer';
  const isViewer = userRole.toLowerCase() === 'viewer';

  useEffect(() => {
    dispatch(fetchProjects())
      .unwrap()
      .catch((err) => setSnackbarMessage('Error: ' + (err || 'Failed to fetch projects.')));
  }, [dispatch]);

  const handleCreate = async () => {
    if (!name.trim()) {
      setSnackbarMessage('Error: Project name is required.');
      return;
    }
    setSubmitting(true);
    try {
      await dispatch(createNewProject({
        name: name.trim(),
        project_type: projectType,
        base_url: baseUrl.trim() || undefined
      }) as any).unwrap();
      setSnackbarMessage('Project created successfully.');
      setIsCreateOpen(false);
      setName('');
      setBaseUrl('');
      setProjectType('web_page');
    } catch (err: any) {
      setSnackbarMessage('Error: ' + (err || 'Failed to create project.'));
    } finally {
      setSubmitting(false);
    }
  };

  const filteredProjects = useMemo(() => {
    if (!searchVal) return projects;
    const q = searchVal.toLowerCase();
    return projects.filter((p) => p.name.toLowerCase().includes(q));
  }, [projects, searchVal]);

  const paginatedProjects = useMemo(() => {
    const start = page * rowsPerPage;
    return filteredProjects.slice(start, start + rowsPerPage);
  }, [filteredProjects, page, rowsPerPage]);

  const columns: ColumnDefinition<ProjectResponse>[] = [
    { id: 'name', label: 'Project Name', sortable: false },
    { id: 'project_type', label: 'Target Type', sortable: false },
    { id: 'created_at', label: 'Date Created', sortable: false },
  ];

  const renderRow = (project: ProjectResponse) => {
    const dateFormatted = new Date(project.created_at).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    });

    const isApp = project.project_type === 'web_application';

    return (
      <TableRow key={project.id} hover>
        <TableCell sx={{ fontWeight: '700', color: 'text.primary', py: 2 }}>{project.name}</TableCell>
        <TableCell sx={{ py: 2 }}>
          <Chip
            icon={isApp ? <AppShortcutIcon fontSize="small" /> : <LanguageIcon fontSize="small" />}
            label={isApp ? 'Web Application' : 'Web Page'}
            size="small"
            color={isApp ? 'secondary' : 'primary'}
            variant="outlined"
            sx={{ fontWeight: 600, borderRadius: '6px' }}
          />
        </TableCell>
        <TableCell sx={{ color: 'text.secondary', py: 2 }}>{dateFormatted}</TableCell>
      </TableRow>
    );
  };

  return (
    <Box sx={{ pb: 4 }}>
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" sx={{ fontWeight: 700, color: '#16191f', letterSpacing: '-0.02em', fontSize: '1.875rem', mb: 0.5 }}>
          Projects
        </Typography>
        <Typography variant="body1" sx={{ color: '#545b64', fontWeight: 500 }}>
          Organize accessibility audits, credentials, and compliance reports by project target.
        </Typography>
      </Box>

      {loading && projects.length === 0 ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '300px' }}>
          <CircularProgress color="primary" />
        </Box>
      ) : (
        <Box sx={{ position: 'relative' }}>
          {loading && (
            <LinearProgress
              sx={{ position: 'absolute', top: -8, left: 0, right: 0, borderRadius: 1, height: 3 }}
            />
          )}
          <DataTable
            searchTerm={searchVal}
            onSearchChange={setSearchVal}
            searchPlaceholder="Search projects by name..."
            loading={loading}
            totalCount={filteredProjects.length}
            page={page}
            rowsPerPage={rowsPerPage}
            onPageChange={(_, newPage) => setPage(newPage)}
            onRowsPerPageChange={(newRowsPerPage) => {
              setRowsPerPage(newRowsPerPage);
              setPage(0);
            }}
            columns={columns}
            data={paginatedProjects}
            renderRow={renderRow}
            canCreate={!isViewer}
            createButtonText="New Project"
            onCreateClick={() => {
              setName('');
              setBaseUrl('');
              setProjectType('web_page');
              setIsCreateOpen(true);
            }}
            emptyMessage="No projects yet. Create your first project to get started."
            headerActions={
              <Typography variant="h6" sx={{ color: 'text.primary', fontWeight: '800', fontFamily: 'Outfit' }}>
                All Projects
              </Typography>
            }
          />
        </Box>
      )}

      {/* Create Project Dialog */}
      <Dialog open={isCreateOpen} onClose={() => !submitting && setIsCreateOpen(false)} fullWidth maxWidth="sm">
        <DialogTitle sx={{ fontWeight: '800' }}>Create New Project</DialogTitle>
        <DialogContent>
          <Stack spacing={3} sx={{ mt: 1 }}>
            <TextField
              label="Project Name"
              fullWidth
              autoFocus
              value={name}
              onChange={(e) => setName(e.target.value)}
              disabled={submitting}
              placeholder="e.g. Customer Portal Audit"
            />

            <FormControl component="fieldset">
              <FormLabel sx={{ fontWeight: 700, color: 'text.primary', mb: 1 }}>Project Target Type</FormLabel>
              <RadioGroup
                row
                value={projectType}
                onChange={(e) => setProjectType(e.target.value as 'web_page' | 'web_application')}
              >
                <Paper
                  variant="outlined"
                  sx={{
                    p: 1.5,
                    mr: 2,
                    borderRadius: 2,
                    borderColor: projectType === 'web_page' ? 'primary.main' : 'divider',
                    bgcolor: projectType === 'web_page' ? 'action.hover' : 'background.paper',
                    cursor: 'pointer'
                  }}
                  onClick={() => setProjectType('web_page')}
                >
                  <FormControlLabel
                    value="web_page"
                    control={<Radio color="primary" />}
                    label={
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <LanguageIcon color="primary" fontSize="small" />
                        <Box>
                          <Typography variant="body2" sx={{ fontWeight: 700 }}>Web Page</Typography>
                          <Typography variant="caption" color="text.secondary">Public website discovery & audit</Typography>
                        </Box>
                      </Box>
                    }
                  />
                </Paper>

                <Paper
                  variant="outlined"
                  sx={{
                    p: 1.5,
                    borderRadius: 2,
                    borderColor: projectType === 'web_application' ? 'secondary.main' : 'divider',
                    bgcolor: projectType === 'web_application' ? 'action.hover' : 'background.paper',
                    cursor: 'pointer'
                  }}
                  onClick={() => setProjectType('web_application')}
                >
                  <FormControlLabel
                    value="web_application"
                    control={<Radio color="secondary" />}
                    label={
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <AppShortcutIcon color="secondary" fontSize="small" />
                        <Box>
                          <Typography variant="body2" sx={{ fontWeight: 700 }}>Web Application</Typography>
                          <Typography variant="caption" color="text.secondary">Public + Auth protected portal audit</Typography>
                        </Box>
                      </Box>
                    }
                  />
                </Paper>
              </RadioGroup>
            </FormControl>

            <TextField
              label="Base / Target URL"
              fullWidth
              value={baseUrl}
              onChange={(e) => setBaseUrl(e.target.value)}
              disabled={submitting}
              placeholder="https://app.example.com"
              helperText={projectType === 'web_application' ? 'For Web Applications, you will be prompted to add test credentials during the audit workflow.' : 'Starting URL for public page crawler.'}
            />
          </Stack>
        </DialogContent>
        <DialogActions sx={{ p: 3 }}>
          <Button onClick={() => setIsCreateOpen(false)} variant="outlined" disabled={submitting} sx={{ textTransform: 'none', borderRadius: '8px' }}>
            Cancel
          </Button>
          <Button onClick={handleCreate} variant="contained" color="primary" disabled={submitting} sx={{ color: 'white', textTransform: 'none', borderRadius: '8px' }}>
            {submitting ? 'Creating...' : 'Create Project'}
          </Button>
        </DialogActions>
      </Dialog>

      <Snackbar
        open={!!snackbarMessage}
        autoHideDuration={4000}
        onClose={() => setSnackbarMessage('')}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert
          severity={snackbarMessage.startsWith('Error') ? 'error' : 'success'}
          sx={{ width: '100%', borderRadius: '8px', boxShadow: 3 }}
        >
          {snackbarMessage}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default ProjectsPage;
