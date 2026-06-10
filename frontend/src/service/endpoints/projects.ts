import api from '../api';
import type {
  ProjectResponse,
  ApiKeyResponse,
  ApiKeyCreatedResponse,
} from '../../model/project.model';
import type {
  DashboardStats,
  HistoricalTrends,
} from '../../model/dashboard.model';
import type {
  BillingStatus,
} from '../../model/billing.model';

export type {
  ProjectResponse,
  ApiKeyResponse,
  ApiKeyCreatedResponse,
} from '../../model/project.model';
export type {
  DashboardStats,
  HistoricalTrends,
} from '../../model/dashboard.model';
export type {
  BillingTransaction,
  BillingStatus,
} from '../../model/billing.model';

export const projectService = {
  listProjects: async (): Promise<ProjectResponse[]> => {
    const response = await api.get<ProjectResponse[]>('/api/projects');
    return response.data;
  },

  createProject: async (name: string): Promise<ProjectResponse> => {
    const response = await api.post<ProjectResponse>('/api/projects', { name });
    return response.data;
  },

  listApiKeys: async (): Promise<ApiKeyResponse[]> => {
    const response = await api.get<ApiKeyResponse[]>('/api/keys');
    return response.data;
  },

  createApiKey: async (name: string, expiresInDays: number = 30): Promise<ApiKeyCreatedResponse> => {
    const response = await api.post<ApiKeyCreatedResponse>('/api/keys', { name, expires_in_days: expiresInDays });
    return response.data;
  },

  revokeApiKey: async (id: string): Promise<void> => {
    await api.delete(`/api/keys/${id}`);
  },

  getDashboardStats: async (): Promise<DashboardStats> => {
    const response = await api.get<DashboardStats>('/api/dashboard/stats');
    return response.data;
  },

  getHistoricalTrends: async (): Promise<HistoricalTrends> => {
    const response = await api.get<HistoricalTrends>('/api/trends');
    return response.data;
  },

  getBillingStatus: async (): Promise<BillingStatus> => {
    const response = await api.get<BillingStatus>('/api/billing/status');
    return response.data;
  },

  topupCredits: async (packageName: string, amountUsd: number): Promise<any> => {
    const response = await api.post<any>('/api/billing/topup', { package_name: packageName, amount_usd: amountUsd });
    return response.data;
  },

  togglePayAsYouGo: async (): Promise<any> => {
    const response = await api.post<any>('/api/billing/toggle-pay-as-you-go');
    return response.data;
  },
};
