import React, { useState } from 'react';
import { useLocation, useNavigate } from '@tanstack/react-router';
import {
  Box,
  List,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Avatar,
  Typography,
  Menu,
  MenuItem,
  useTheme
} from '@mui/material';
import { alpha } from '@mui/material/styles';
import DashboardIcon from '@mui/icons-material/Dashboard';
import AssessmentIcon from '@mui/icons-material/Assessment';
import SmartToyIcon from '@mui/icons-material/SmartToy';
import KeyboardArrowDownIcon from '@mui/icons-material/KeyboardArrowDown';
import LogoutIcon from '@mui/icons-material/Logout';
import PaymentIcon from '@mui/icons-material/Payment';
import AccountBalanceWalletIcon from '@mui/icons-material/AccountBalanceWallet';
import KeyIcon from '@mui/icons-material/Key';
import ChecklistIcon from '@mui/icons-material/Checklist';
import PeopleIcon from '@mui/icons-material/People';
import LockIcon from '@mui/icons-material/Lock';
import FolderIcon from '@mui/icons-material/Folder';
import { useAppDispatch } from '../../../store';
import { logoutUser } from '../../../store/slices/authSlice';

interface SidebarProps {
  onNavClick?: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ onNavClick }) => {
  const navigate = useNavigate();
  const location = useLocation();
  const dispatch = useAppDispatch();
  const theme = useTheme();
  const [profileAnchorEl, setProfileAnchorEl] = useState<null | HTMLElement>(null);

  const handleProfileClick = (event: React.MouseEvent<HTMLElement>) => {
    setProfileAnchorEl(event.currentTarget);
  };

  const handleProfileClose = () => {
    setProfileAnchorEl(null);
  };

  const handleSignOut = () => {
    dispatch(logoutUser());
    navigate({ to: '/auth/signin' });
  };

  const email = localStorage.getItem('user_email') || 'user@example.com';
  const role = localStorage.getItem('user_role') || 'Viewer';
  const formattedName = email
    .split('@')[0]
    .split('.')
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(' ');

  const currentPath = location.pathname;

  const handleNav = (path: string) => {
    if (path === '/maintenance') {
      navigate({ to: '/maintenance' });
    } else {
      navigate({ to: path as any });
    }
    if (onNavClick) {
      onNavClick();
    }
  };

  const orgId = localStorage.getItem('org_id') || 'default';

  const showUserManagement = role.toLowerCase() === 'admin' || role.toLowerCase() === 'superadmin';

  const menuItems = [
    { text: 'Dashboard', icon: <DashboardIcon />, path: `/org/${orgId}/dashboard` },
    { text: 'Projects', icon: <FolderIcon />, path: `/org/${orgId}/projects` },
    { text: 'Audits', icon: <ChecklistIcon />, path: `/org/${orgId}/audits` },
    { text: 'Agents', icon: <SmartToyIcon />, path: `/org/${orgId}/agents` },
    { text: 'Billing', icon: <PaymentIcon />, path: `/org/${orgId}/billing` },
    { text: 'Credits', icon: <AccountBalanceWalletIcon />, path: `/org/${orgId}/credits` },
    ...(showUserManagement ? [{ text: 'Users', icon: <PeopleIcon />, path: `/org/${orgId}/users` }] : []),
    { text: 'Credentials', icon: <LockIcon />, path: `/org/${orgId}/credentials` },
    { text: 'API Keys', icon: <KeyIcon />, path: `/org/${orgId}/api-keys` },
  ];

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', height: '100%', bgcolor: 'text.primary', color: 'primary.contrastText' }}>
      {/* Sidebar Header */}
      <Box sx={{ p: 3, display: 'flex', alignItems: 'center', gap: 1.5 }}>
        <Box sx={{
          width: 40,
          height: 40,
          borderRadius: '8px',
          bgcolor: 'primary.main',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: 'primary.contrastText',
          boxShadow: `0 4px 10px ${alpha(theme.palette.primary.main, 0.3)}`
        }}>
          <AssessmentIcon sx={{ fontSize: '1.5rem' }} />
        </Box>
        <Box>
          <Typography variant="h6" sx={{ color: 'primary.contrastText', fontWeight: '800', lineHeight: 1.1 }}>
            A11ySense AI
          </Typography>
          <Typography variant="caption" sx={{ color: 'text.secondary', fontWeight: '500' }}>
            Enterprise Audit
          </Typography>
        </Box>
      </Box>

      {/* Navigation List */}
      <List sx={{ px: 2, flexGrow: 1 }}>
        {menuItems.map((item) => {
          const active = currentPath === item.path;
          return (
            <ListItemButton
              key={item.text}
              onClick={() => handleNav(item.path)}
              sx={{
                borderRadius: '8px',
                mb: 1,
                px: 2,
                py: 1.2,
                position: 'relative',
                bgcolor: active ? alpha(theme.palette.primary.main, 0.15) : 'transparent',
                color: active ? 'primary.contrastText' : 'text.disabled',
                '&:hover': {
                  bgcolor: alpha(theme.palette.primary.contrastText, 0.05),
                  color: 'primary.contrastText',
                  '& .MuiListItemIcon-root': { color: 'primary.contrastText' }
                },
                '& .MuiListItemIcon-root': {
                  color: active ? 'primary.main' : 'text.secondary',
                  minWidth: 40
                }
              }}
            >
              {active && (
                <Box sx={{
                  position: 'absolute',
                  left: 0,
                  top: '15%',
                  height: '70%',
                  width: 4,
                  bgcolor: 'primary.main',
                  borderRadius: '0 4px 4px 0'
                }} />
              )}
              <ListItemIcon>{item.icon}</ListItemIcon>
              <ListItemText>
                <Typography sx={{ fontSize: '0.92rem', fontWeight: active ? '700' : '600', color: active ? 'primary.contrastText' : 'text.disabled' }}>
                  {item.text}
                </Typography>
              </ListItemText>
            </ListItemButton>
          );
        })}
      </List>

      {/* User Profile Footer */}
      <Box sx={{ p: 2, borderTop: '1px solid', borderColor: alpha(theme.palette.primary.contrastText, 0.1) }}>
        <Box
          onClick={handleProfileClick}
          sx={{
            display: 'flex',
            alignItems: 'center',
            gap: 1.5,
            p: 1.5,
            borderRadius: '12px',
            cursor: 'pointer',
            transition: 'background-color 0.2s',
            '&:hover': {
              bgcolor: alpha(theme.palette.primary.contrastText, 0.05)
            }
          }}
        >
          <Avatar
            sx={{
              width: 40,
              height: 40,
              bgcolor: 'primary.main',
              color: 'primary.contrastText',
              fontSize: '1rem',
              fontWeight: '700'
            }}
          >
            {formattedName.split(' ').map((n) => n[0]).join('')}
          </Avatar>
          <Box sx={{ flexGrow: 1, overflow: 'hidden' }}>
            <Typography variant="body2" sx={{ color: 'primary.contrastText', fontWeight: '700', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
              {formattedName}
            </Typography>
            <Typography variant="caption" sx={{ color: 'text.secondary', fontWeight: '700', textTransform: 'uppercase', display: 'block', fontSize: '0.72rem', letterSpacing: '0.5px' }}>
              {role} ACCOUNT
            </Typography>
          </Box>
          <KeyboardArrowDownIcon sx={{ color: 'text.secondary', fontSize: '1.2rem' }} />
        </Box>
      </Box>

      {/* Profile Popup Menu */}
      <Menu
        anchorEl={profileAnchorEl}
        open={Boolean(profileAnchorEl)}
        onClose={handleProfileClose}
        anchorOrigin={{
          vertical: 'top',
          horizontal: 'right',
        }}
        transformOrigin={{
          vertical: 'bottom',
          horizontal: 'left',
        }}
        slotProps={{
          paper: {
            sx: {
              mt: -1.5,
              ml: 1.5,
              bgcolor: 'text.primary',
              color: 'primary.contrastText',
              border: '1px solid',
              borderColor: alpha(theme.palette.primary.contrastText, 0.1),
              boxShadow: '0 10px 25px rgba(0,0,0,0.5)',
              '& .MuiMenuItem-root': {
                fontSize: '0.9rem',
                fontWeight: '600',
                color: 'text.disabled',
                py: 1,
                px: 2.5,
                '&:hover': {
                  bgcolor: alpha(theme.palette.primary.contrastText, 0.05),
                  color: 'primary.contrastText'
                }
              }
            }
          }
        }}
      >
        <MenuItem onClick={() => { handleProfileClose(); navigate({ to: '/maintenance' }); }}>Settings</MenuItem>
        <MenuItem onClick={() => { handleProfileClose(); handleSignOut(); }} sx={{ color: 'error.main' }}>
          <ListItemIcon sx={{ color: 'error.main', minWidth: 28 }}><LogoutIcon fontSize="small" /></ListItemIcon>
          Sign Out
        </MenuItem>
      </Menu>
    </Box>
  );
};
