export interface AuditRequest {
  url: string;
  depth?: number;
  audit_type?: 'standard' | 'comprehensive';
  credentials_id?: string;
}

export interface AuditTask {
  task_id: string;
  status: 'processing' | 'crawling' | 'auditing' | 'completed' | 'failed' | string;
  url?: string;
  report_url?: string;
  created_at?: string;
  pages_found?: number;
  pages_completed?: number;
  pages_total?: number;
  pages_scanned?: string[];
  pages_discovered?: string[];
  pages_depth_map?: Record<string, number>;
  error?: string;
  token_usage?: any;
}
