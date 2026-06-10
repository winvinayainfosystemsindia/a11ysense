import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import type { MetricsState } from '../../model/metrics.model';
import { metricsService } from '../../service/endpoints/metrics';

const initialState: MetricsState = {
  metrics: [],
  loading: false,
  error: null,
  lastUpdated: null,
};

export const fetchSystemMetrics = createAsyncThunk(
  'metrics/fetchSystemMetrics',
  async (_, { rejectWithValue }) => {
    try {
      const data = await metricsService.getSystemMetrics();
      return data;
    } catch (err: any) {
      return rejectWithValue(err.response?.data?.message || err.message || 'Failed to fetch metrics');
    }
  }
);

const metricsSlice = createSlice({
  name: 'metrics',
  initialState,
  reducers: {},
  extraReducers: (builder) => {
    builder
      .addCase(fetchSystemMetrics.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchSystemMetrics.fulfilled, (state, action) => {
        state.loading = false;
        state.metrics = action.payload;
        state.lastUpdated = new Date().toISOString();
      })
      .addCase(fetchSystemMetrics.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      });
  },
});

export default metricsSlice.reducer;
