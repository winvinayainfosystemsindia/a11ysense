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
  run_number?: number;
  run_type?: string;
  previous_run_id?: string | null;
  previous_run_number?: number | null;
  score?: number;
  score_delta?: number;
  defects_new?: number;
  defects_fixed?: number;
  defects_reopened?: number;
  defects_open?: number;
  defects_not_retested?: number;
  created_at?: string;
  pages_found?: number;
  pages_completed?: number;
  pages_total?: number;
  pages_scanned?: string[];
  pages_discovered?: string[];
  pages_depth_map?: Record<string, number>;
  error?: string;
  summary?: any;
  token_usage?: TokenUsage;
}

export interface ProviderUsage {
  calls: number;
  cached_calls?: number;
  input_tokens: number;
  output_tokens: number;
  total_tokens: number;
  cost_usd: number;
  label?: string;
}

export interface CategoryUsage {
  category: string;
  label: string;
  calls: number;
  cached_calls?: number;
  input_tokens: number;
  output_tokens: number;
  total_tokens: number;
  cost_usd: number;
}

export interface MatrixItem {
  category: string;
  category_label: string;
  provider: string;
  provider_label: string;
  model: string;
  calls: number;
  cached_calls?: number;
  input_tokens: number;
  output_tokens: number;
  total_tokens: number;
  cost_usd: number;
}

export interface TokenUsage {
  task_id?: string;
  tokens_total: number;
  tokens_sent?: number;
  tokens_received?: number;
  tokens_prompt?: number;
  tokens_completion?: number;
  llm_calls?: number;
  cached_calls?: number;
  cost_usd_total?: number;
  cost_estimate_usd?: number;
  cost_by_provider?: Record<string, ProviderUsage>;
  cost_by_category?: Record<string, CategoryUsage>;
  breakdown?: Record<string, any>;
  matrix?: MatrixItem[];
  totals?: {
    calls: number;
    cached_calls?: number;
    input_tokens: number;
    output_tokens: number;
    total_tokens: number;
    cost_usd: number;
  };
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

  getTaskTestcases: async (taskId: string): Promise<any> => {
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

