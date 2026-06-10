export interface LogItem {
  time: string;
  agent: string;
  message: string;
  type: 'success' | 'info' | 'error';
  task_id: string;
  status: string;
  pages_completed?: number;
  pages_total?: number;
}

export interface ActiveTask {
  task_id: string;
  status: string;
  url: string;
  pages_completed: number;
  pages_total: number;
  created_at: string | null;
}

export interface TelemetryStats {
  active_agents_count: number;
  active_tasks: ActiveTask[];
  total_tasks_run: number;
  completed_tasks_run: number;
  failed_tasks_run: number;
  total_violations_found: number;
  tokens: {
    input_tokens: number;
    output_tokens: number;
    total_tokens: number;
  };
}
