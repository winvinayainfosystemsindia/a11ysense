import api from '../api';
import type { ProjectCreate, ProjectResponse } from '../../model/project.model';
import type { DashboardStats, HistoricalTrends } from '../../model/dashboard.model';

export type { ProjectResponse } from '../../model/project.model';
export type { DashboardStats, HistoricalTrends } from '../../model/dashboard.model';

export const projectService = {
  listProjects: async (): Promise<ProjectResponse[]> => {
    const response = await api.get<ProjectResponse[]>('/api/projects');
    return response.data;
  },

  createProject: async (payload: string | ProjectCreate): Promise<ProjectResponse> => {
    const reqData = typeof payload === 'string' ? { name: payload } : payload;
    const response = await api.post<ProjectResponse>('/api/projects', reqData);
    return response.data;
  },

  getDashboardStats: async (range?: string): Promise<DashboardStats> => {
    const response = await api.get<DashboardStats>('/api/dashboard/stats', {
      params: range ? { time_range: range } : undefined
    });
    return response.data;
  },

  getHistoricalTrends: async (range?: string): Promise<HistoricalTrends> => {
    const response = await api.get<HistoricalTrends>('/api/trends', {
      params: range ? { time_range: range } : undefined
    });
    return response.data;
  },
};
