import api from './api';

export interface AuditSessionInfo {
  task_id: string;
  url: string;
  timestamp: string;
  status: string;
  accessibility_score: number;
  total_violations: number;
  project_name: string;
}

export interface AuditTaskDetail {
  task_id: string;
  url: string;
  depth: number;
  status: string;
  created_at?: string;
  pages_found?: number;
  pages_completed?: number;
  pages_total?: number;
  pages_scanned?: string[];
  pages_discovered?: string[];
  pages_depth_map?: Record<string, number>;
  error?: string;
  summary?: any;
}

export interface TokenUsage {
  tokens_total: number;
  tokens_prompt: number;
  tokens_completion: number;
  cost_estimate_usd: number;
}

export const auditService = {
  getAudits: async (): Promise<AuditSessionInfo[]> => {
    const response = await api.get('/api/audits');
    return response.data;
  },

  getTaskStatus: async (taskId: string): Promise<AuditTaskDetail> => {
    const response = await api.get(`/task/${taskId}`);
    return response.data;
  },

  getTokenUsage: async (taskId: string): Promise<TokenUsage> => {
    const response = await api.get(`/task/${taskId}/token_usage`);
    return response.data;
  },

  getTaskTestcases: async (taskId: string): Promise<any[]> => {
    const response = await api.get(`/task/${taskId}/testcases`);
    return response.data;
  },

  stopAudit: async (taskId: string): Promise<any> => {
    const response = await api.post(`/task/${taskId}/stop`);
    return response.data;
  },

  pauseAudit: async (taskId: string): Promise<any> => {
    const response = await api.post(`/task/${taskId}/pause`);
    return response.data;
  },

  resumeAudit: async (taskId: string): Promise<any> => {
    const response = await api.post(`/task/${taskId}/resume`);
    return response.data;
  },

  deleteAudit: async (taskId: string): Promise<any> => {
    const response = await api.delete(`/task/${taskId}`);
    return response.data;
  }
};

