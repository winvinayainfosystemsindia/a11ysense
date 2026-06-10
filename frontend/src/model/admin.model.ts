export interface ErrorLog {
  id: string;
  correlation_id: string;
  service_name: string;
  severity: string;
  message: string;
  timestamp: string;
  context_json: string;
}

export interface AdminErrorsStatsResponse {
  total_errors: number;
  critical_count: number;
  error_count: number;
  service_breakdown: Record<string, number>;
  latest_logs: ErrorLog[];
}
