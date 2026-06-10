import axios from 'axios';
import { ENV } from '../../config/env';
import type { PrometheusMetric } from '../../model/metrics.model';

function parsePrometheusText(text: string): PrometheusMetric[] {
  const lines = text.split('\n');
  const metrics: PrometheusMetric[] = [];
  
  let currentHelp = '';
  let currentType = '';

  for (const line of lines) {
    const trimmed = line.trim();
    if (!trimmed) continue;

    if (trimmed.startsWith('# HELP')) {
      const parts = trimmed.substring(7).split(' ');
      // The first part is the metric name, the rest is help text
      currentHelp = parts.slice(1).join(' ');
      continue;
    }

    if (trimmed.startsWith('# TYPE')) {
      const parts = trimmed.substring(7).split(' ');
      if (parts.length > 1) {
        currentType = parts[1];
      }
      continue;
    }

    if (trimmed.startsWith('#')) {
      continue; // Skip any other comments
    }

    // Parse metric line: name{label="value"} value
    // e.g. process_virtual_memory_bytes 12345
    // e.g. http_requests_total{method="GET",status="200"} 5
    
    // Values can be NaN, +Inf, -Inf, etc.
    const lastSpaceIndex = trimmed.lastIndexOf(' ');
    if (lastSpaceIndex === -1) continue;

    const valueStr = trimmed.substring(lastSpaceIndex + 1);
    let value = parseFloat(valueStr);
    if (valueStr === 'NaN') value = NaN;
    else if (valueStr === '+Inf') value = Infinity;
    else if (valueStr === '-Inf') value = -Infinity;
    
    const nameAndLabels = trimmed.substring(0, lastSpaceIndex).trim();
    
    let name = nameAndLabels;
    const labels: Record<string, string> = {};

    const braceIndex = nameAndLabels.indexOf('{');
    if (braceIndex !== -1 && nameAndLabels.endsWith('}')) {
      name = nameAndLabels.substring(0, braceIndex);
      const labelsStr = nameAndLabels.substring(braceIndex + 1, nameAndLabels.length - 1);
      
      const labelRegex = /([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*"([^"\\]*(?:\\.[^"\\]*)*)"/g;
      let match;
      while ((match = labelRegex.exec(labelsStr)) !== null) {
        labels[match[1]] = match[2];
      }
    }

    metrics.push({
      name,
      value,
      labels,
      type: currentType,
      help: currentHelp,
    });
  }

  return metrics;
}

export const metricsService = {
  getSystemMetrics: async (): Promise<PrometheusMetric[]> => {
    // Determine metrics URL based on API_URL
    // from http://localhost:8000/v1 to http://localhost:8000/metrics
    const baseUrl = ENV.API_URL.endsWith('/v1') 
      ? ENV.API_URL.slice(0, -3) 
      : ENV.API_URL;
      
    const metricsUrl = `${baseUrl}/metrics`;

    const response = await axios.get(metricsUrl, {
      headers: {
        Accept: 'text/plain',
      },
    });

    return parsePrometheusText(response.data);
  },
};
