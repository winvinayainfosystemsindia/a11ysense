import React from 'react';
import {
  Card,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
  IconButton,
  Chip,
  Box,
  Tooltip,
  alpha
} from '@mui/material';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import DeleteIcon from '@mui/icons-material/Delete';

interface ApiKey {
  id: string;
  name: string;
  key?: string;
  created_at: string;
  expires_at: string | null;
  status: 'active' | 'revoked';
}

interface ApiKeysListProps {
  apiKeys: ApiKey[];
  onCopy: (key: string) => void;
  onRevoke: (id: string) => void;
}

const ApiKeysList: React.FC<ApiKeysListProps> = ({ apiKeys, onCopy, onRevoke }) => {
  return (
    <Card variant="outlined" sx={{ bgcolor: 'background.paper', borderRadius: '12px' }}>
      <TableContainer>
        <Table sx={{ minWidth: 650 }}>
          <TableHead>
            <TableRow sx={{ bgcolor: (theme) => alpha(theme.palette.primary.main, 0.03) }}>
              <TableCell sx={{ fontWeight: '700', color: 'text.secondary' }}>NAME</TableCell>
              <TableCell sx={{ fontWeight: '700', color: 'text.secondary' }}>SECRET KEY</TableCell>
              <TableCell sx={{ fontWeight: '700', color: 'text.secondary' }}>CREATED</TableCell>
              <TableCell sx={{ fontWeight: '700', color: 'text.secondary' }}>EXPIRES</TableCell>
              <TableCell sx={{ fontWeight: '700', color: 'text.secondary' }}>STATUS</TableCell>
              <TableCell align="right" sx={{ fontWeight: '700', color: 'text.secondary' }}>ACTIONS</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {apiKeys.length === 0 ? (
              <TableRow>
                <TableCell colSpan={6} align="center" sx={{ py: 6 }}>
                  <Typography variant="body1" color="text.secondary">
                    No API keys found. Generate a new key to get started.
                  </Typography>
                </TableCell>
              </TableRow>
            ) : (
              apiKeys.map((apiKey) => (
                <TableRow key={apiKey.id} sx={{ '&:last-child td, &:last-child th': { border: 0 }, '&:hover': { bgcolor: (theme) => alpha(theme.palette.primary.main, 0.01) } }}>
                  <TableCell>
                    <Typography variant="subtitle2" sx={{ fontWeight: '600' }}>
                      {apiKey.name}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <Typography sx={{ fontFamily: 'monospace', bgcolor: 'action.hover', px: 1, py: 0.5, borderRadius: '4px' }}>
                        {apiKey.key || '••••••••••••••••••••••••'}
                      </Typography>
                      <Tooltip title="Copy Key">
                        <IconButton size="small" onClick={() => onCopy(apiKey.key || '')}>
                          <ContentCopyIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>
                    </Box>
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2" color="text.secondary">
                      {new Date(apiKey.created_at).toLocaleDateString()}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2" color="text.secondary">
                      {apiKey.expires_at ? new Date(apiKey.expires_at).toLocaleDateString() : 'Never'}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Chip
                      label={apiKey.status.toUpperCase()}
                      size="small"
                      color={apiKey.status === 'active' ? 'success' : 'default'}
                      sx={{ fontWeight: '700', fontSize: '0.7rem' }}
                    />
                  </TableCell>
                  <TableCell align="right">
                    {apiKey.status === 'active' && (
                      <Tooltip title="Revoke Key">
                        <IconButton size="small" color="error" onClick={() => onRevoke(apiKey.id)}>
                          <DeleteIcon />
                        </IconButton>
                      </Tooltip>
                    )}
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </TableContainer>
    </Card>
  );
};

export default ApiKeysList;
