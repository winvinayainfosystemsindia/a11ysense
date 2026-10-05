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
  pages: EstimatedPage[];
  summary: EstimationSummary;
}

export interface DiscoveredUrlItem {
  url: string;
  path: string;
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
}

export interface RecalculateParams {
  pages: EstimatedPage[];
  hourly_rate?: number;
  platform_fee?: number;
  profit_margin_pct?: number;
}

export const estimationService = {
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

  downloadQuotationExcel: async (data: EstimationResult): Promise<void> => {
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

  downloadQuotationPdf: async (data: EstimationResult): Promise<void> => {
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
