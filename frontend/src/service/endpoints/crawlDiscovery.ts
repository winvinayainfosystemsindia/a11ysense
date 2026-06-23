import api from '../api';
import type { CrawlDiscoveryRequest, CrawlDiscoveryTask } from '../../model/audit.model';

export const crawlDiscoveryService = {
  startCrawlDiscovery: async (request: CrawlDiscoveryRequest, projectId?: string): Promise<CrawlDiscoveryTask> => {
    const url = projectId ? `/crawl_discovery?project_id=${projectId}` : '/crawl_discovery';
    const response = await api.post<CrawlDiscoveryTask>(url, request);
    return response.data;
  },

  getCrawlDiscoveryStatus: async (crawlTaskId: string): Promise<CrawlDiscoveryTask> => {
    const response = await api.get<CrawlDiscoveryTask>(`/crawl_discovery/${crawlTaskId}`);
    return response.data;
  },
};
