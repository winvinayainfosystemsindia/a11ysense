import api from './api';
import type {
  RegressionSummary,
  ProjectRun,
  ProjectTrendItem,
  DefectDetail,
  RunComparison
} from '../model/regression.model';

export const regressionService = {
  getRegressionSummary: async (taskId: string): Promise<RegressionSummary> => {
    const response = await api.get<RegressionSummary>(`/api/audits/${taskId}/regression`);
    return response.data;
  },

  compareAudits: async (taskIdA: string, taskIdB: string): Promise<RunComparison> => {
    const response = await api.get<RunComparison>(`/api/audits/${taskIdA}/compare/${taskIdB}`);
    return response.data;
  },

  getProjectRuns: async (projectId: string): Promise<ProjectRun[]> => {
    const response = await api.get<ProjectRun[]>(`/api/projects/${projectId}/runs`);
    return response.data;
  },

  getProjectTrend: async (projectId: string): Promise<{ runs: ProjectTrendItem[] }> => {
    const response = await api.get<{ runs: ProjectTrendItem[] }>(`/api/projects/${projectId}/trend`);
    return response.data;
  },

  getProjectDefects: async (
    projectId: string,
    params?: { status?: string; severity?: string }
  ): Promise<any[]> => {
    const response = await api.get<any[]>(`/api/projects/${projectId}/defects`, { params });
    return response.data;
  },

  getDefectDetail: async (defectId: string): Promise<DefectDetail> => {
    const response = await api.get<DefectDetail>(`/api/defects/${defectId}`);
    return response.data;
  },

  updateDefectStatus: async (
    defectId: string,
    status: string,
    reason?: string,
    auditSessionId?: string
  ): Promise<any> => {
    const response = await api.patch<any>(`/api/defects/${defectId}`, {
      status,
      reason,
      audit_session_id: auditSessionId
    });
    return response.data;
  }
};
