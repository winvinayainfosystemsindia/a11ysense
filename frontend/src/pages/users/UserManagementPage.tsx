import React, { useState, useEffect, useMemo } from 'react';
import {
  Box,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Button,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  IconButton,
  Tooltip,
  TableRow,
  TableCell,
  Snackbar,
  Alert,
  Typography,
  CircularProgress,
  LinearProgress,
  Stack
} from '@mui/material';
import EditIcon from '@mui/icons-material/Edit';
import DeleteIcon from '@mui/icons-material/Delete';
import StatusBadge from '../../components/common/badge/StatusBadge';
import DataTable, { type ColumnDefinition } from '../../components/common/table/DataTable';
import { userService } from '../../service/endpoints/users';
import type { UserResponse, OrganizationResponse } from '../../model/users.model';

const UserManagementPage: React.FC = () => {
  const [users, setUsers] = useState<UserResponse[]>([]);
  const [organizations, setOrganizations] = useState<OrganizationResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [snackbarMessage, setSnackbarMessage] = useState('');
  const [searchVal, setSearchVal] = useState('');

  // Form states
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [isEditOpen, setIsEditOpen] = useState(false);
  const [selectedUser, setSelectedUser] = useState<UserResponse | null>(null);

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [role, setRole] = useState('Viewer');
  const [orgId, setOrgId] = useState('');

  const myEmail = localStorage.getItem('user_email') || '';
  const myRole = localStorage.getItem('user_role') || 'Viewer';
  const isSuperadmin = myRole.toLowerCase() === 'superadmin';

  // Pagination states
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);

  const fetchUsersAndOrgs = async () => {
    setLoading(true);
    try {
      const usersData = await userService.listUsers();
      setUsers(usersData);

      if (isSuperadmin) {
        const orgsData = await userService.listOrganizations();
        setOrganizations(orgsData);
      }
    } catch (err: any) {
      console.error(err);
      setSnackbarMessage('Error: ' + (err.userMessage || 'Failed to fetch users.'));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUsersAndOrgs();
  }, []);

  const handleCreate = async () => {
    if (!email || !password) {
      setSnackbarMessage('Error: Email and password are required.');
      return;
    }
    try {
      await userService.createUser({
        email,
        password,
        role,
        organization_id: isSuperadmin && orgId ? orgId : undefined
      });
      setSnackbarMessage('User created successfully.');
      setIsCreateOpen(false);
      // Reset form
      setEmail('');
      setPassword('');
      setRole('Viewer');
      setOrgId('');
      fetchUsersAndOrgs();
    } catch (err: any) {
      console.error(err);
      setSnackbarMessage('Error: ' + (err.userMessage || 'Failed to create user.'));
    }
  };

  const handleEditOpen = (user: UserResponse) => {
    setSelectedUser(user);
    setEmail(user.email);
    setRole(user.role);
    setOrgId(user.organization_id);
    setIsEditOpen(true);
  };

  const handleUpdate = async () => {
    if (!selectedUser) return;
    try {
      await userService.updateUser(selectedUser.id, {
        email,
        role,
        organization_id: isSuperadmin ? orgId : undefined
      });
      setSnackbarMessage('User updated successfully.');
      setIsEditOpen(false);
      setSelectedUser(null);
      setEmail('');
      setRole('Viewer');
      setOrgId('');
      fetchUsersAndOrgs();
    } catch (err: any) {
      console.error(err);
      setSnackbarMessage('Error: ' + (err.userMessage || 'Failed to update user.'));
    }
  };

  const handleDelete = async (id: string, userEmail: string) => {
    if (userEmail === myEmail) {
      setSnackbarMessage('Error: You cannot delete your own account.');
      return;
    }
    if (!window.confirm(`Are you sure you want to delete the user account for ${userEmail}?`)) {
      return;
    }
    try {
      await userService.deleteUser(id);
      setSnackbarMessage('User deleted successfully.');
      fetchUsersAndOrgs();
    } catch (err: any) {
      console.error(err);
      setSnackbarMessage('Error: ' + (err.userMessage || 'Failed to delete user.'));
    }
  };

  // Filter users based on search
  const filteredUsers = useMemo(() => {
    if (!searchVal) return users;
    const q = searchVal.toLowerCase();
    return users.filter(u => 
      u.email.toLowerCase().includes(q) || 
      u.role.toLowerCase().includes(q) || 
      u.organization_name.toLowerCase().includes(q)
    );
  }, [users, searchVal]);

  const paginatedUsers = useMemo(() => {
    const start = page * rowsPerPage;
    return filteredUsers.slice(start, start + rowsPerPage);
  }, [filteredUsers, page, rowsPerPage]);

  const columns: ColumnDefinition<UserResponse>[] = [
    { id: 'email', label: 'Email', sortable: false },
    { id: 'role', label: 'Role', sortable: false },
    { id: 'organization_name', label: 'Organization', sortable: false },
    { id: 'created_at', label: 'Date Joined', sortable: false },
    { id: 'actions' as any, label: 'Actions', align: 'right', sortable: false }
  ];

  const getBadgeStatus = (roleStr: string) => {
    const r = roleStr.toLowerCase();
    if (r === 'superadmin' || r === 'admin') return 'active';
    if (r === 'auditor') return 'prospect';
    return 'default';
  };

  const renderRow = (user: UserResponse) => {
    const isSelf = user.email === myEmail;
    const dateFormatted = new Date(user.created_at).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    });

    return (
      <TableRow key={user.id} hover>
        <TableCell sx={{ fontWeight: '700', color: 'text.primary', py: 2 }}>
          {user.email} {isSelf && <span style={{ color: '#888', fontWeight: 'normal' }}>(You)</span>}
        </TableCell>
        <TableCell sx={{ py: 2 }}>
          <StatusBadge
            label={user.role}
            status={getBadgeStatus(user.role)}
            type="generic"
          />
        </TableCell>
        <TableCell sx={{ color: 'text.secondary', py: 2 }}>{user.organization_name}</TableCell>
        <TableCell sx={{ color: 'text.secondary', py: 2 }}>{dateFormatted}</TableCell>
        <TableCell align="right" sx={{ py: 1 }}>
          <Box sx={{ display: 'flex', justifyContent: 'flex-end', gap: 0.5 }}>
            <Tooltip title="Edit User">
              <IconButton
                size="small"
                onClick={() => handleEditOpen(user)}
                sx={{ color: 'text.secondary', '&:hover': { color: 'primary.main' } }}
              >
                <EditIcon fontSize="small" />
              </IconButton>
            </Tooltip>
            <Tooltip title={isSelf ? "Cannot delete self" : "Delete User"}>
              <span>
                <IconButton
                  size="small"
                  onClick={() => handleDelete(user.id, user.email)}
                  disabled={isSelf}
                  sx={{ 
                    color: 'text.disabled', 
                    '&:hover': { color: isSelf ? 'text.disabled' : 'error.main' } 
                  }}
                >
                  <DeleteIcon fontSize="small" />
                </IconButton>
              </span>
            </Tooltip>
          </Box>
        </TableCell>
      </TableRow>
    );
  };

  return (
    <Box sx={{ pb: 4 }}>
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" sx={{ fontWeight: 700, color: '#16191f', letterSpacing: '-0.02em', fontSize: '1.875rem', mb: 0.5 }}>
          User Management
        </Typography>
        <Typography variant="body1" sx={{ color: '#545b64', fontWeight: 500 }}>
          Manage your organization's user accounts, roles, and access controls.
        </Typography>
      </Box>

      {loading && users.length === 0 ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '300px' }}>
          <CircularProgress color="primary" />
        </Box>
      ) : (
        <Box sx={{ position: 'relative' }}>
          {loading && (
            <LinearProgress
              sx={{
                position: 'absolute',
                top: -8,
                left: 0,
                right: 0,
                borderRadius: 1,
                height: 3
              }}
            />
          )}
          <DataTable
            searchTerm={searchVal}
            onSearchChange={setSearchVal}
            searchPlaceholder="Search users by email or role..."
            loading={loading}
            totalCount={filteredUsers.length}
            page={page}
            rowsPerPage={rowsPerPage}
            onPageChange={(_, newPage) => setPage(newPage)}
            onRowsPerPageChange={(newRowsPerPage) => {
              setRowsPerPage(newRowsPerPage);
              setPage(0);
            }}
            columns={columns}
            data={paginatedUsers}
            renderRow={renderRow}
            canCreate={true}
            createButtonText="Add User"
            onCreateClick={() => {
              setEmail('');
              setPassword('');
              setRole('Viewer');
              setOrgId(organizations[0]?.id || '');
              setIsCreateOpen(true);
            }}
            headerActions={
              <Typography variant="h6" sx={{ color: 'text.primary', fontWeight: '800', fontFamily: 'Outfit' }}>
                All Users {isSuperadmin ? '(Global System)' : ''}
              </Typography>
            }
          />
        </Box>
      )}

      {/* Create User Dialog */}
      <Dialog open={isCreateOpen} onClose={() => setIsCreateOpen(false)} fullWidth maxWidth="sm">
        <DialogTitle sx={{ fontWeight: '800' }}>Add New User</DialogTitle>
        <DialogContent>
          <Stack spacing={3} sx={{ mt: 1 }}>
            <TextField
              label="Email Address"
              type="email"
              fullWidth
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
            <TextField
              label="Password"
              type="password"
              fullWidth
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
            <FormControl fullWidth>
              <InputLabel>Role</InputLabel>
              <Select
                value={role}
                label="Role"
                onChange={(e) => setRole(e.target.value)}
              >
                <MenuItem value="Admin">Admin</MenuItem>
                <MenuItem value="Auditor">Auditor</MenuItem>
                <MenuItem value="Viewer">Viewer</MenuItem>
                {isSuperadmin && <MenuItem value="Superadmin">Superadmin</MenuItem>}
              </Select>
            </FormControl>

            {isSuperadmin && (
              <FormControl fullWidth>
                <InputLabel>Organization</InputLabel>
                <Select
                  value={orgId}
                  label="Organization"
                  onChange={(e) => setOrgId(e.target.value)}
                >
                  {organizations.map(org => (
                    <MenuItem key={org.id} value={org.id}>{org.name}</MenuItem>
                  ))}
                </Select>
              </FormControl>
            )}
          </Stack>
        </DialogContent>
        <DialogActions sx={{ p: 3 }}>
          <Button onClick={() => setIsCreateOpen(false)} variant="outlined" sx={{ textTransform: 'none', borderRadius: '8px' }}>
            Cancel
          </Button>
          <Button onClick={handleCreate} variant="contained" color="primary" sx={{ color: 'white', textTransform: 'none', borderRadius: '8px' }}>
            Create User
          </Button>
        </DialogActions>
      </Dialog>

      {/* Edit User Dialog */}
      <Dialog open={isEditOpen} onClose={() => setIsEditOpen(false)} fullWidth maxWidth="sm">
        <DialogTitle sx={{ fontWeight: '800' }}>Edit User Details</DialogTitle>
        <DialogContent>
          <Stack spacing={3} sx={{ mt: 1 }}>
            <TextField
              label="Email Address"
              type="email"
              fullWidth
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
            <FormControl fullWidth>
              <InputLabel>Role</InputLabel>
              <Select
                value={role}
                label="Role"
                onChange={(e) => setRole(e.target.value)}
              >
                <MenuItem value="Admin">Admin</MenuItem>
                <MenuItem value="Auditor">Auditor</MenuItem>
                <MenuItem value="Viewer">Viewer</MenuItem>
                {isSuperadmin && <MenuItem value="Superadmin">Superadmin</MenuItem>}
              </Select>
            </FormControl>

            {isSuperadmin && (
              <FormControl fullWidth>
                <InputLabel>Organization</InputLabel>
                <Select
                  value={orgId}
                  label="Organization"
                  onChange={(e) => setOrgId(e.target.value)}
                >
                  {organizations.map(org => (
                    <MenuItem key={org.id} value={org.id}>{org.name}</MenuItem>
                  ))}
                </Select>
              </FormControl>
            )}
          </Stack>
        </DialogContent>
        <DialogActions sx={{ p: 3 }}>
          <Button onClick={() => setIsEditOpen(false)} variant="outlined" sx={{ textTransform: 'none', borderRadius: '8px' }}>
            Cancel
          </Button>
          <Button onClick={handleUpdate} variant="contained" color="primary" sx={{ color: 'white', textTransform: 'none', borderRadius: '8px' }}>
            Save Changes
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

export default UserManagementPage;
