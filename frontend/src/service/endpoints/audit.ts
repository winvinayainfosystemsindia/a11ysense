import api from '../api';
import type { AuditRequest, AuditTask } from '../../model/audit.model';

export type { AuditRequest, AuditTask } from '../../model/audit.model';

export const auditService = {
  startAudit: async (request: AuditRequest, projectId?: string): Promise<AuditTask> => {
    const url = projectId ? `/start_audit?project_id=${projectId}` : '/start_audit';
    const response = await api.post<AuditTask>(url, request);
    return response.data;
  },

  getTaskStatus: async (taskId: string): Promise<AuditTask> => {
    const response = await api.get<AuditTask>(`/task/${taskId}`);
    return response.data;
  },

  getTaskTokenUsage: async (taskId: string): Promise<any> => {
    const response = await api.get<any>(`/task/${taskId}/token_usage`);
    return response.data;
  },

  getTaskTestcases: async (taskId: string): Promise<any> => {
    const response = await api.get<any>(`/task/${taskId}/testcases`);
    return response.data;
  },
};
