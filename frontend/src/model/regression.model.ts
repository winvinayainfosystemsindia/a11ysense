export interface RegressionSummary {
  has_previous_run: boolean;
  run_number: number;
  previous_run_number: number | null;
  score: number;
  previous_score: number;
  score_delta: number;
  defects_new: number;
  defects_fixed: number;
  defects_reopened: number;
  defects_open: number;
  defects_not_retested: number;
}

export interface ProjectRun {
  id: string;
  task_id: string;
  run_number: number;
  run_type: 'baseline' | 'regression';
  score: number;
  score_delta: number;
  defects_new: number;
  defects_fixed: number;
  defects_reopened: number;
  defects_open: number;
  defects_not_retested: number;
  status: string;
  completed_at: string | null;
  previous_run_id: string | null;
}

export interface ProjectTrendItem {
  run_number: number;
  run_type: string;
  score: number;
  defects_new: number;
  defects_fixed: number;
  defects_reopened: number;
  defects_open: number;
  completed_at: string | null;
}

export interface DefectEventItem {
  id: string;
  event: string;
  from_status: string | null;
  to_status: string;
  note: string | null;
  created_at: string;
  audit_session_id: string | null;
}

export interface DefectDetail {
  id: string;
  defect_code: string;
  status: 'New' | 'Open' | 'Fixed' | 'Closed' | 'WontFix' | 'FalsePositive';
  severity: string;
  rule_id: string;
  sc_code: string;
  sc_name: string;
  title: string;
  page_url: string;
  times_seen: number;
  reopen_count: number;
  age_days: number;
  first_seen_run_number: number;
  last_seen_run_number: number;
  fixed_in_run_number: number | null;
  code_before: string;
  code_after: string;
  fix_steps: string[];
  verify_steps: string[];
  false_positive_note: string;
  timeline: DefectEventItem[];
}

export interface RunComparison {
  run_a: {
    task_id: string;
    run_number: number;
    score: number;
    url: string;
  };
  run_b: {
    task_id: string;
    run_number: number;
    score: number;
    url: string;
  };
  score_delta: number;
  fixed_in_b: any[];
  new_in_b: any[];
  common_open: any[];
}
