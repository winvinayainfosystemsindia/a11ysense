import api from './api';

export interface CredentialCreate {
  label: string;
  login_url: string;
  url_pattern: string;
  auth_type: string;
  username?: string;
  password?: string;
  username_field?: string;
  password_field?: string;
  submit_selector?: string;
  post_login_url_pattern?: string;
  extra_fields?: Record<string, string>;
}

export interface Credential {
  id: string;
  project_id: string;
  organization_id: string;
  label: string;
  login_url: string;
  url_pattern: string;
  auth_type: string;
  username_masked?: string;
  username_field?: string;
  password_field?: string;
  submit_selector?: string;
  post_login_url_pattern?: string;
  has_extra_fields: boolean;
  created_at: string;
  updated_at: string;
}

export const credentialService = {
  async getCredentials(projectId: string): Promise<Credential[]> {
    const response = await api.get(`/api/projects/${projectId}/credentials`);
    return response.data;
  },

  async createCredential(projectId: string, req: CredentialCreate): Promise<Credential> {
    const response = await api.post(`/api/projects/${projectId}/credentials`, req);
    return response.data;
  },

  async updateCredential(projectId: string, credentialId: string, req: CredentialCreate): Promise<Credential> {
    const response = await api.put(`/api/projects/${projectId}/credentials/${credentialId}`, req);
    return response.data;
  },

  async deleteCredential(projectId: string, credentialId: string): Promise<void> {
    await api.delete(`/api/projects/${projectId}/credentials/${credentialId}`);
  },

  async testCredential(projectId: string, credentialId: string): Promise<any> {
    const response = await api.post(`/api/projects/${projectId}/credentials/${credentialId}/test`);
    return response.data;
  }
};
