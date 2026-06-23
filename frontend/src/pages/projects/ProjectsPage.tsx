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
  Stack
} from '@mui/material';
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
  const [name, setName] = useState('');
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
      await dispatch(createNewProject(name.trim())).unwrap();
      setSnackbarMessage('Project created successfully.');
      setIsCreateOpen(false);
      setName('');
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
    { id: 'created_at', label: 'Date Created', sortable: false },
  ];

  const renderRow = (project: ProjectResponse) => {
    const dateFormatted = new Date(project.created_at).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    });

    return (
      <TableRow key={project.id} hover>
        <TableCell sx={{ fontWeight: '700', color: 'text.primary', py: 2 }}>{project.name}</TableCell>
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
          Organize audits, credentials, and reports by project.
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
        <DialogTitle sx={{ fontWeight: '800' }}>New Project</DialogTitle>
        <DialogContent>
          <Stack spacing={3} sx={{ mt: 1 }}>
            <TextField
              label="Project Name"
              fullWidth
              autoFocus
              value={name}
              onChange={(e) => setName(e.target.value)}
              disabled={submitting}
              onKeyDown={(e) => {
                if (e.key === 'Enter') handleCreate();
              }}
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
