import api from './api';

export interface ApiKey {
  id: string;
  name: string;
  created_at: string;
  expires_at: string | null;
  key?: string; // Only available immediately after creation
  status?: 'active' | 'revoked'; // Inferred from existence
}

export const apiKeysService = {
  async getApiKeys(): Promise<ApiKey[]> {
    const response = await api.get('/api/keys');
    // Backend only returns active keys, revoked keys are deleted
    return response.data.map((key: any) => ({
      ...key,
      status: 'active',
      key: '••••••••••••••••••••••••', // Masked for security as backend doesn't return the raw key here
    }));
  },

  async generateApiKey(name: string): Promise<ApiKey> {
    const response = await api.post('/api/keys', {
      name,
      expires_in_days: 30, // Default to 30 days expiration
    });
    
    // Response contains 'api_key' which is the raw secret
    return {
      id: response.data.id,
      name: response.data.name,
      created_at: response.data.created_at,
      expires_at: response.data.expires_at,
      key: response.data.api_key,
      status: 'active',
    };
  },

  async revokeApiKey(id: string): Promise<void> {
    await api.delete(`/api/keys/${id}`);
  }
};
