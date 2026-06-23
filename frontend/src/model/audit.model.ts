export type ScanTarget = 'web_page' | 'web_application' | 'both';

export interface AuditRequest {
  url: string;
  depth?: number;
  audit_type?: 'standard' | 'comprehensive' | ScanTarget;
  credentials_id?: string;
  selected_urls?: string[];
  crawl_task_id?: string;
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

export interface CrawlDiscoveryRequest {
  url: string;
  scan_target: ScanTarget;
  credentials_id?: string;
}

export interface CrawlDiscoveryTask {
  crawl_task_id: string;
  status: 'queued' | 'crawling' | 'completed' | 'failed' | string;
  url: string;
  pages_discovered: string[];
  pages_depth_map?: Record<string, number>;
  url_to_menu_text?: Record<string, string>;
  sitemaps_found?: string[];
  unauth_pages_discovered?: string[];
  auth_pages_discovered?: string[];
  error?: string;
  created_at?: string;
}
