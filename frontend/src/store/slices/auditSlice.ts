import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import type { PayloadAction } from '@reduxjs/toolkit';
import { auditService } from '../../service/endpoints/audit';
import type { AuditRequest, AuditTask } from '../../model/audit.model';

interface AuditState {
  currentTask: AuditTask | null;
  tokenUsage: any;
  testCases: any;
  loading: boolean;
  error: string | null;
}

const initialState: AuditState = {
  currentTask: null,
  tokenUsage: null,
  testCases: null,
  loading: false,
  error: null,
};

export const initiateAudit = createAsyncThunk(
  'audit/initiateAudit',
  async (payload: { request: AuditRequest; projectId?: string }, { rejectWithValue }) => {
    try {
      return await auditService.startAudit(payload.request, payload.projectId);
    } catch (err: any) {
      return rejectWithValue(err.userMessage || 'Failed to start accessibility audit scan');
    }
  }
);

export const fetchTaskStatus = createAsyncThunk(
  'audit/fetchTaskStatus',
  async (taskId: string, { rejectWithValue }) => {
    try {
      return await auditService.getTaskStatus(taskId);
    } catch (err: any) {
      return rejectWithValue(err.userMessage || 'Failed to poll audit task status');
    }
  }
);

export const fetchTaskTokenUsage = createAsyncThunk(
  'audit/fetchTaskTokenUsage',
  async (taskId: string, { rejectWithValue }) => {
    try {
      return await auditService.getTaskTokenUsage(taskId);
    } catch (err: any) {
      return rejectWithValue(err.userMessage || 'Failed to fetch audit LLM token usage');
    }
  }
);

export const fetchTaskTestcases = createAsyncThunk(
  'audit/fetchTaskTestcases',
  async (taskId: string, { rejectWithValue }) => {
    try {
      return await auditService.getTaskTestcases(taskId);
    } catch (err: any) {
      return rejectWithValue(err.userMessage || 'Failed to fetch audit test case report');
    }
  }
);

const auditSlice = createSlice({
  name: 'audit',
  initialState,
  reducers: {
    clearAuditTask(state) {
      state.currentTask = null;
      state.tokenUsage = null;
      state.testCases = null;
      state.error = null;
    },
    clearAuditError(state) {
      state.error = null;
    }
  },
  extraReducers: (builder) => {
    builder
      // Start Audit
      .addCase(initiateAudit.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(initiateAudit.fulfilled, (state, action: PayloadAction<AuditTask>) => {
        state.loading = false;
        state.currentTask = action.payload;
      })
      .addCase(initiateAudit.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      })
      // Poll Task Status
      .addCase(fetchTaskStatus.fulfilled, (state, action: PayloadAction<AuditTask>) => {
        state.currentTask = action.payload;
      })
      .addCase(fetchTaskStatus.rejected, (state, action) => {
        state.error = action.payload as string;
      })
      // Fetch Token Usage
      .addCase(fetchTaskTokenUsage.fulfilled, (state, action) => {
        state.tokenUsage = action.payload;
      })
      // Fetch Test cases
      .addCase(fetchTaskTestcases.fulfilled, (state, action) => {
        state.testCases = action.payload;
      });
  },
});

export const { clearAuditTask, clearAuditError } = auditSlice.actions;
export default auditSlice.reducer;
