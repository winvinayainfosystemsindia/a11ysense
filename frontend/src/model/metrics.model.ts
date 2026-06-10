export interface PrometheusMetric {
  name: string;
  value: number;
  labels: Record<string, string>;
  type?: string;
  help?: string;
}

export interface MetricsState {
  metrics: PrometheusMetric[];
  loading: boolean;
  error: string | null;
  lastUpdated: string | null;
}
