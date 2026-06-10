import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import type { PayloadAction } from '@reduxjs/toolkit';
import { adminService } from '../../service/endpoints/admin';
import type { AdminErrorsStatsResponse } from '../../model/admin.model';

interface AdminState {
  errorStats: AdminErrorsStatsResponse | null;
  loading: boolean;
  error: string | null;
}

const initialState: AdminState = {
  errorStats: null,
  loading: false,
  error: null,
};

export const fetchAdminErrorsStats = createAsyncThunk(
  'admin/fetchErrorsStats',
  async (_, { rejectWithValue }) => {
    try {
      return await adminService.getErrorsStats();
    } catch (err: any) {
      return rejectWithValue(err.userMessage || 'Failed to fetch admin error stats');
    }
  }
);

const adminSlice = createSlice({
  name: 'admin',
  initialState,
  reducers: {
    clearAdminError(state) {
      state.error = null;
    }
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchAdminErrorsStats.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchAdminErrorsStats.fulfilled, (state, action: PayloadAction<AdminErrorsStatsResponse>) => {
        state.loading = false;
        state.errorStats = action.payload;
      })
      .addCase(fetchAdminErrorsStats.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      });
  },
});

export const { clearAdminError } = adminSlice.actions;
export default adminSlice.reducer;
