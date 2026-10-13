import api from './api';

export interface PageCounts {
  links: number;
  buttons: number;
  headings: number;
  paragraphs: number;
  lists: number;
  images: number;
  forms: number;
  inputs: number;
  tables: number;
  media: number;
  total_elements: number;
}

export interface EstimatedPage {
  url: string;
  title: string;
  complexity: 'simple' | 'medium' | 'complex';
  complexity_label: string;
  summary_rationale: string;
  triggers: string[];
  counts: PageCounts;
  manual_hours: number;
  manual_cost: number;
  api_cost: number;
  platform_cost: number;
  base_cost: number;
  profit_margin: number;
  final_cost: number;
  status: string;
  error?: string | null;
}

export interface EstimationSummary {
  total_pages: number;
  simple_pages: number;
  medium_pages: number;
  complex_pages: number;
  hourly_rate: number;
  platform_fee_per_page: number;
  profit_margin_pct: number;
  total_manual_hours: number;
  total_manual_cost: number;
  total_api_cost: number;
  total_platform_cost: number;
  total_base_cost: number;
  total_profit_margin: number;
  total_final_cost: number;
}

export interface EstimationResult {
  id?: string;
  title?: string;
  base_url?: string;
  mode?: string;
  status?: string;
  pages: EstimatedPage[];
  summary: EstimationSummary;
  created_at?: string;
  updated_at?: string;
}

export interface SavedEstimateRecord {
  id: string;
  title: string;
  base_url: string;
  mode: string;
  status: string;
  hourly_rate: number;
  platform_fee: number;
  profit_margin_pct: number;
  total_pages: number;
  simple_pages: number;
  medium_pages: number;
  complex_pages: number;
  total_manual_hours: number;
  total_manual_cost: number;
  total_api_cost: number;
  total_platform_cost: number;
  total_base_cost: number;
  total_profit_margin: number;
  total_quote: number;
  summary?: EstimationSummary;
  pages?: EstimatedPage[];
  created_at: string;
  updated_at?: string;
}

export interface DiscoveredUrlItem {
  url: string;
  title?: string;
  path?: string;
}

export interface DiscoverResult {
  base_url: string;
  total_found: number;
  urls: DiscoveredUrlItem[];
}

export interface DiscoverParams {
  url: string;
  depth?: number;
  max_pages?: number;
}

export interface AnalyzeParams {
  url?: string;
  urls?: string[];
  depth?: number;
  max_pages?: number;
  hourly_rate?: number;
  platform_fee?: number;
  profit_margin_pct?: number;
  title?: string;
  base_url?: string;
  mode?: string;
  save_to_db?: boolean;
  org_id?: string;
}

export interface RecalculateParams {
  pages: EstimatedPage[];
  hourly_rate?: number;
  platform_fee?: number;
  profit_margin_pct?: number;
}

export interface SaveEstimatePayload {
  title: string;
  base_url: string;
  mode: string;
  hourly_rate: number;
  platform_fee: number;
  profit_margin_pct: number;
  pages: EstimatedPage[];
  summary: EstimationSummary;
  org_id?: string;
}

export interface UpdateEstimatePayload {
  title?: string;
  hourly_rate?: number;
  platform_fee?: number;
  profit_margin_pct?: number;
  pages?: EstimatedPage[];
}

export const estimationService = {
  list: async (orgId?: string): Promise<SavedEstimateRecord[]> => {
    const params = orgId ? { org_id: orgId } : {};
    const response = await api.get('/api/estimation', { params });
    return response.data;
  },

  get: async (estimateId: string): Promise<SavedEstimateRecord & { pages: EstimatedPage[]; summary: EstimationSummary }> => {
    const response = await api.get(`/api/estimation/${estimateId}`);
    return response.data;
  },

  save: async (data: SaveEstimatePayload): Promise<SavedEstimateRecord> => {
    const response = await api.post('/api/estimation/save', data);
    return response.data;
  },

  update: async (estimateId: string, data: UpdateEstimatePayload): Promise<SavedEstimateRecord & { pages: EstimatedPage[]; summary: EstimationSummary }> => {
    const response = await api.put(`/api/estimation/${estimateId}`, data);
    return response.data;
  },

  delete: async (estimateId: string): Promise<void> => {
    await api.delete(`/api/estimation/${estimateId}`);
  },

  discover: async (params: DiscoverParams): Promise<DiscoverResult> => {
    const response = await api.post('/api/estimation/discover', params);
    return response.data;
  },

  analyze: async (params: AnalyzeParams): Promise<EstimationResult> => {
    const response = await api.post('/api/estimation/analyze', params);
    return response.data;
  },

  recalculate: async (params: RecalculateParams): Promise<EstimationResult> => {
    const response = await api.post('/api/estimation/recalculate', params);
    return response.data;
  },

  downloadQuotationExcel: async (data: { summary: EstimationSummary; pages: EstimatedPage[] }): Promise<void> => {
    const response = await api.post('/api/estimation/export/excel', data, {
      responseType: 'blob',
    });
    const blob = new Blob([response.data], {
      type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    const dateStr = new Date().toISOString().slice(0, 10);
    link.setAttribute('download', `A11ySense_Quotation_${dateStr}.xlsx`);
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
  },

  downloadQuotationPdf: async (data: { summary: EstimationSummary; pages: EstimatedPage[] }): Promise<void> => {
    const response = await api.post('/api/estimation/export/pdf', data, {
      responseType: 'blob',
    });
    const blob = new Blob([response.data], {
      type: 'application/pdf',
    });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    const dateStr = new Date().toISOString().slice(0, 10);
    link.setAttribute('download', `A11ySense_Quotation_${dateStr}.pdf`);
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
  }
};
