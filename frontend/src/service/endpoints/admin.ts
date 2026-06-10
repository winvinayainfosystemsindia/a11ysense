import api from '../api';
import type { AdminErrorsStatsResponse } from '../../model/admin.model';

export type { AdminErrorsStatsResponse, ErrorLog } from '../../model/admin.model';

export const adminService = {
  getErrorsStats: async (): Promise<AdminErrorsStatsResponse> => {
    const response = await api.get<AdminErrorsStatsResponse>('/api/admin/errors/stats');
    return response.data;
  },
};
