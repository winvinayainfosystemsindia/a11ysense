export interface DashboardStats {
  total_audits: number;
  completed_audits_count: number;
  failed_audits_count: number;
  active_audits_count: number;
  average_score: number;
  total_violations: number;
  violations_by_impact: {
    critical: number;
    serious: number;
    moderate: number;
    minor: number;
    [key: string]: number;
  };
  total_tokens_used: number;
  recent_audits: Array<{
    task_id: string;
    url: string;
    timestamp: string;
    status: string;
    accessibility_score: number;
    total_violations: number;
    project_name: string;
  }>;
}

export interface HistoricalTrends {
  score_trend: Array<{
    date: string;
    score: number;
    url: string;
  }>;
  violation_trend: Array<{
    date: string;
    violations: number;
    url: string;
  }>;
}
