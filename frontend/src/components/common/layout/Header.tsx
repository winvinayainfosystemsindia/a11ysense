import React, { useState } from 'react';
import { StartAuditDialog } from '../../audit/StartAuditDialog';
import {
  Box,
  IconButton,
  TextField,
  InputAdornment,
  Badge,
  Button
} from '@mui/material';
import SearchIcon from '@mui/icons-material/Search';
import AddIcon from '@mui/icons-material/Add';
import NotificationsNoneIcon from '@mui/icons-material/NotificationsNone';
import HelpIcon from '@mui/icons-material/Help';
import MenuIcon from '@mui/icons-material/Menu';

interface HeaderProps {
  isMobile: boolean;
  onMenuClick: () => void;
}

export const Header: React.FC<HeaderProps> = ({ isMobile, onMenuClick }) => {
  const [auditDialogOpen, setAuditDialogOpen] = useState(false);

  return (
    <Box
      sx={{
        height: 70,
        bgcolor: 'background.paper',
        borderBottom: '1px solid',
        borderBottomColor: 'divider',
        px: { xs: 2, sm: 4 },
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        position: 'sticky',
        top: 0,
        zIndex: 1100
      }}
    >
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, flexGrow: 1 }}>
        {isMobile && (
          <IconButton onClick={onMenuClick} edge="start" sx={{ color: 'text.secondary' }}>
            <MenuIcon />
          </IconButton>
        )}
        <TextField
          size="small"
          placeholder="Search audits or files..."
          variant="outlined"
          sx={{
            width: { xs: '100%', sm: 300 },
            '& .MuiOutlinedInput-root': {
              bgcolor: 'background.default',
              borderRadius: '8px',
              '& fieldset': { borderColor: 'divider' },
              '&:hover fieldset': { borderColor: 'text.disabled' },
              '&.Mui-focused fieldset': { borderColor: 'primary.main' },
            },
            '& .MuiInputBase-input': {
              fontSize: '0.85rem',
              fontWeight: '500',
              py: 1
            }
          }}
          slotProps={{
            input: {
              startAdornment: (
                <InputAdornment position="start">
                  <SearchIcon sx={{ color: 'text.disabled', fontSize: '1.1rem' }} />
                </InputAdornment>
              ),
            }
          }}
        />
      </Box>

      <Box sx={{ display: 'flex', alignItems: 'center', gap: { xs: 1, sm: 2 } }}>
        <Button
          variant="contained"
          color="primary"
          onClick={() => {
            setAuditDialogOpen(true);
          }}
          startIcon={<AddIcon />}
          sx={{
            fontWeight: '700',
            fontSize: '0.85rem',
            textTransform: 'none',
            borderRadius: '8px',
            px: 2,
            py: 0.8
          }}
        >
          New Audit
        </Button>

        <Box sx={{ display: 'flex', alignItems: 'center', borderLeft: '1px solid', borderLeftColor: 'divider', pl: 2, gap: 1 }}>
          <IconButton sx={{ color: 'text.secondary' }}>
            <Badge variant="dot" color="error">
              <NotificationsNoneIcon />
            </Badge>
          </IconButton>
          <IconButton sx={{ color: 'text.secondary' }}>
            <HelpIcon />
          </IconButton>
        </Box>
      </Box>
      <StartAuditDialog open={auditDialogOpen} onClose={() => setAuditDialogOpen(false)} />
    </Box>
  );
};
