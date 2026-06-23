import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import type { PayloadAction } from '@reduxjs/toolkit';
import { crawlDiscoveryService } from '../../service/endpoints/crawlDiscovery';
import type { CrawlDiscoveryRequest, CrawlDiscoveryTask } from '../../model/audit.model';

interface CrawlDiscoveryState {
  currentCrawlTask: CrawlDiscoveryTask | null;
  loading: boolean;
  error: string | null;
}

const initialState: CrawlDiscoveryState = {
  currentCrawlTask: null,
  loading: false,
  error: null,
};

export const initiateCrawlDiscovery = createAsyncThunk(
  'crawlDiscovery/initiate',
  async (payload: { request: CrawlDiscoveryRequest; projectId?: string }, { rejectWithValue }) => {
    try {
      return await crawlDiscoveryService.startCrawlDiscovery(payload.request, payload.projectId);
    } catch (err: any) {
      return rejectWithValue(err.userMessage || 'Failed to start page discovery crawl');
    }
  }
);

export const fetchCrawlDiscoveryStatus = createAsyncThunk(
  'crawlDiscovery/fetchStatus',
  async (crawlTaskId: string, { rejectWithValue }) => {
    try {
      return await crawlDiscoveryService.getCrawlDiscoveryStatus(crawlTaskId);
    } catch (err: any) {
      return rejectWithValue(err.userMessage || 'Failed to poll page discovery status');
    }
  }
);

const crawlDiscoverySlice = createSlice({
  name: 'crawlDiscovery',
  initialState,
  reducers: {
    clearCrawlTask(state) {
      state.currentCrawlTask = null;
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(initiateCrawlDiscovery.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(initiateCrawlDiscovery.fulfilled, (state, action: PayloadAction<CrawlDiscoveryTask>) => {
        state.loading = false;
        state.currentCrawlTask = action.payload;
      })
      .addCase(initiateCrawlDiscovery.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      })
      .addCase(fetchCrawlDiscoveryStatus.fulfilled, (state, action: PayloadAction<CrawlDiscoveryTask>) => {
        state.currentCrawlTask = action.payload;
      })
      .addCase(fetchCrawlDiscoveryStatus.rejected, (state, action) => {
        state.error = action.payload as string;
      });
  },
});

export const { clearCrawlTask } = crawlDiscoverySlice.actions;
export default crawlDiscoverySlice.reducer;
