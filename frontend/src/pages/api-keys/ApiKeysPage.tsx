import React, { useState, useEffect } from 'react';
import { Box, Stack, Snackbar, Alert, CircularProgress, Typography } from '@mui/material';
import ApiKeysHeader from '../../components/api-keys/ApiKeysHeader';
import ApiKeysList from '../../components/api-keys/ApiKeysList';
import GenerateKeyModal from '../../components/api-keys/GenerateKeyModal';
import { apiKeysService } from '../../service/apiKeysService';
import type { ApiKey } from '../../service/apiKeysService';

const ApiKeysPage: React.FC = () => {
  const [apiKeys, setApiKeys] = useState<ApiKey[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [snackbarMessage, setSnackbarMessage] = useState('');

  // Fetch keys on mount
  useEffect(() => {
    const fetchKeys = async () => {
      try {
        const data = await apiKeysService.getApiKeys();
        setApiKeys(data);
      } catch (err) {
        console.error('Failed to fetch API keys', err);
        setSnackbarMessage('Error: Could not load API keys from the server.');
      } finally {
        setIsLoading(false);
      }
    };
    fetchKeys();
  }, []);

  const handleGenerateKey = async (name: string) => {
    try {
      const newKey = await apiKeysService.generateApiKey(name);
      setApiKeys((prev) => [newKey, ...prev]);
      setSnackbarMessage(`Successfully generated key: ${name}`);
    } catch (err) {
      console.error('Failed to generate API key', err);
      setSnackbarMessage('Error: Could not generate a new API key.');
    }
  };

  const handleCopyKey = (key: string) => {
    navigator.clipboard.writeText(key);
    setSnackbarMessage('API key copied to clipboard');
  };

  const handleRevokeKey = async (id: string) => {
    try {
      await apiKeysService.revokeApiKey(id);
      setApiKeys((prevKeys) =>
        prevKeys.map((k) => (k.id === id ? { ...k, status: 'revoked' as const } : k))
      );
      setSnackbarMessage('API key successfully revoked');
    } catch (err) {
      console.error('Failed to revoke API key', err);
      setSnackbarMessage('Error: Could not revoke the API key.');
    }
  };

  return (
    <Box sx={{ pb: 4 }}>
      <ApiKeysHeader onGenerate={() => setIsModalOpen(true)} />
      
      <Stack component="div" spacing={4} sx={{ mt: 4 }}>
        {isLoading ? (
          <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', py: 8 }}>
            <CircularProgress color="primary" />
            <Typography variant="body2" color="text.secondary" sx={{ mt: 2, fontWeight: '500' }}>
              Fetching secure keys...
            </Typography>
          </Box>
        ) : (
          <ApiKeysList apiKeys={apiKeys as any} onCopy={handleCopyKey} onRevoke={handleRevokeKey} />
        )}
      </Stack>

      <GenerateKeyModal
        open={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onGenerate={handleGenerateKey}
      />

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

export default ApiKeysPage;
