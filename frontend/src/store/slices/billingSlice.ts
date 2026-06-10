import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import type { PayloadAction } from '@reduxjs/toolkit';
import { projectService } from '../../service/endpoints/projects';
import type { BillingStatus } from '../../model/billing.model';

interface BillingState {
  billingStatus: BillingStatus | null;
  loading: boolean;
  error: string | null;
}

const initialState: BillingState = {
  billingStatus: null,
  loading: false,
  error: null,
};

export const fetchBillingStatus = createAsyncThunk(
  'billing/fetchBillingStatus',
  async (_, { rejectWithValue }) => {
    try {
      return await projectService.getBillingStatus();
    } catch (err: any) {
      return rejectWithValue(err.userMessage || 'Failed to fetch billing status');
    }
  }
);

export const purchaseTopup = createAsyncThunk(
  'billing/purchaseTopup',
  async (payload: { packageName: string; amountUsd: number }, { rejectWithValue }) => {
    try {
      return await projectService.topupCredits(payload.packageName, payload.amountUsd);
    } catch (err: any) {
      return rejectWithValue(err.userMessage || 'Failed to complete topup transaction');
    }
  }
);

export const toggleOverage = createAsyncThunk(
  'billing/toggleOverage',
  async (_, { rejectWithValue }) => {
    try {
      return await projectService.togglePayAsYouGo();
    } catch (err: any) {
      return rejectWithValue(err.userMessage || 'Failed to toggle Pay-As-You-Go status');
    }
  }
);

const billingSlice = createSlice({
  name: 'billing',
  initialState,
  reducers: {
    clearBillingError(state) {
      state.error = null;
    }
  },
  extraReducers: (builder) => {
    builder
      // Fetch Billing
      .addCase(fetchBillingStatus.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchBillingStatus.fulfilled, (state, action: PayloadAction<BillingStatus>) => {
        state.loading = false;
        state.billingStatus = action.payload;
      })
      .addCase(fetchBillingStatus.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      })
      // Topup
      .addCase(purchaseTopup.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(purchaseTopup.fulfilled, (state) => {
        state.loading = false;
      })
      .addCase(purchaseTopup.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      })
      // Toggle Pay As You Go
      .addCase(toggleOverage.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(toggleOverage.fulfilled, (state) => {
        state.loading = false;
      })
      .addCase(toggleOverage.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      });
  },
});

export const { clearBillingError } = billingSlice.actions;
export default billingSlice.reducer;
