import React, { useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Button,
  Typography,
  IconButton
} from '@mui/material';
import CloseIcon from '@mui/icons-material/Close';

interface GenerateKeyModalProps {
  open: boolean;
  onClose: () => void;
  onGenerate: (name: string) => void;
}

const GenerateKeyModal: React.FC<GenerateKeyModalProps> = ({ open, onClose, onGenerate }) => {
  const [keyName, setKeyName] = useState('');

  const handleGenerate = () => {
    if (keyName.trim()) {
      onGenerate(keyName.trim());
      setKeyName('');
      onClose();
    }
  };

  const handleClose = () => {
    setKeyName('');
    onClose();
  };

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="sm" fullWidth>
      <DialogTitle sx={{ m: 0, p: 2, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography variant="h6" sx={{ fontWeight: '700' }}>
          Generate New API Key
        </Typography>
        <IconButton aria-label="close" onClick={handleClose} sx={{ color: 'text.secondary' }}>
          <CloseIcon />
        </IconButton>
      </DialogTitle>
      <DialogContent dividers sx={{ p: 3 }}>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
          Enter a descriptive name for your new API key to help you identify it later. The key will be generated immediately.
        </Typography>
        <TextField
          autoFocus
          margin="dense"
          id="name"
          label="API Key Name"
          type="text"
          fullWidth
          variant="outlined"
          value={keyName}
          onChange={(e) => setKeyName(e.target.value)}
          placeholder="e.g., CI/CD Pipeline Key"
          sx={{ '& .MuiOutlinedInput-root': { borderRadius: '8px' } }}
        />
      </DialogContent>
      <DialogActions sx={{ p: 2, px: 3 }}>
        <Button onClick={handleClose} sx={{ fontWeight: '600', color: 'text.secondary' }}>
          Cancel
        </Button>
        <Button
          onClick={handleGenerate}
          variant="contained"
          color="primary"
          disabled={!keyName.trim()}
          sx={{ fontWeight: '700', borderRadius: '8px', px: 3 }}
        >
          Generate Key
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default GenerateKeyModal;
