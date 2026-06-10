import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import type { PayloadAction } from '@reduxjs/toolkit';
import { projectService } from '../../service/endpoints/projects';
import type { DashboardStats, HistoricalTrends } from '../../model/dashboard.model';

interface DashboardState {
  stats: DashboardStats | null;
  trends: HistoricalTrends | null;
  loading: boolean;
  error: string | null;
}

const initialState: DashboardState = {
  stats: null,
  trends: null,
  loading: false,
  error: null,
};

export const fetchDashboardStats = createAsyncThunk(
  'dashboard/fetchStats',
  async (_, { rejectWithValue }) => {
    try {
      return await projectService.getDashboardStats();
    } catch (err: any) {
      return rejectWithValue(err.userMessage || 'Failed to fetch dashboard stats');
    }
  }
);

export const fetchHistoricalTrends = createAsyncThunk(
  'dashboard/fetchTrends',
  async (_, { rejectWithValue }) => {
    try {
      return await projectService.getHistoricalTrends();
    } catch (err: any) {
      return rejectWithValue(err.userMessage || 'Failed to fetch historical trends');
    }
  }
);

const dashboardSlice = createSlice({
  name: 'dashboard',
  initialState,
  reducers: {
    clearDashboardError(state) {
      state.error = null;
    }
  },
  extraReducers: (builder) => {
    builder
      // Fetch Stats
      .addCase(fetchDashboardStats.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchDashboardStats.fulfilled, (state, action: PayloadAction<DashboardStats>) => {
        state.loading = false;
        state.stats = action.payload;
      })
      .addCase(fetchDashboardStats.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      })
      // Fetch Trends
      .addCase(fetchHistoricalTrends.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchHistoricalTrends.fulfilled, (state, action: PayloadAction<HistoricalTrends>) => {
        state.loading = false;
        state.trends = action.payload;
      })
      .addCase(fetchHistoricalTrends.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      });
  },
});

export const { clearDashboardError } = dashboardSlice.actions;
export default dashboardSlice.reducer;
