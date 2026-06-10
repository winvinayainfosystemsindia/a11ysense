import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import type { PayloadAction } from '@reduxjs/toolkit';
import { projectService } from '../../service/endpoints/projects';
import type {
  ProjectResponse,
  ApiKeyResponse,
  ApiKeyCreatedResponse
} from '../../model/project.model';

interface ProjectState {
  projects: ProjectResponse[];
  apiKeys: ApiKeyResponse[];
  loading: boolean;
  error: string | null;
}

const initialState: ProjectState = {
  projects: [],
  apiKeys: [],
  loading: false,
  error: null,
};

export const fetchProjects = createAsyncThunk(
  'project/fetchProjects',
  async (_, { rejectWithValue }) => {
    try {
      return await projectService.listProjects();
    } catch (err: any) {
      return rejectWithValue(err.userMessage || 'Failed to fetch projects');
    }
  }
);

export const createNewProject = createAsyncThunk(
  'project/createNewProject',
  async (name: string, { rejectWithValue }) => {
    try {
      return await projectService.createProject(name);
    } catch (err: any) {
      return rejectWithValue(err.userMessage || 'Failed to create project');
    }
  }
);

export const fetchApiKeys = createAsyncThunk(
  'project/fetchApiKeys',
  async (_, { rejectWithValue }) => {
    try {
      return await projectService.listApiKeys();
    } catch (err: any) {
      return rejectWithValue(err.userMessage || 'Failed to fetch API keys');
    }
  }
);

export const createNewApiKey = createAsyncThunk(
  'project/createNewApiKey',
  async (payload: { name: string; expiresInDays?: number }, { rejectWithValue }) => {
    try {
      return await projectService.createApiKey(payload.name, payload.expiresInDays);
    } catch (err: any) {
      return rejectWithValue(err.userMessage || 'Failed to generate API key');
    }
  }
);

export const revokeExistingApiKey = createAsyncThunk(
  'project/revokeExistingApiKey',
  async (id: string, { rejectWithValue }) => {
    try {
      await projectService.revokeApiKey(id);
      return id;
    } catch (err: any) {
      return rejectWithValue(err.userMessage || 'Failed to revoke API key');
    }
  }
);

const projectSlice = createSlice({
  name: 'project',
  initialState,
  reducers: {
    clearProjectError(state) {
      state.error = null;
    }
  },
  extraReducers: (builder) => {
    builder
      // Fetch Projects
      .addCase(fetchProjects.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchProjects.fulfilled, (state, action: PayloadAction<ProjectResponse[]>) => {
        state.loading = false;
        state.projects = action.payload;
      })
      .addCase(fetchProjects.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      })
      // Create Project
      .addCase(createNewProject.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(createNewProject.fulfilled, (state, action: PayloadAction<ProjectResponse>) => {
        state.loading = false;
        state.projects.unshift(action.payload);
      })
      .addCase(createNewProject.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      })
      // Fetch API Keys
      .addCase(fetchApiKeys.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchApiKeys.fulfilled, (state, action: PayloadAction<ApiKeyResponse[]>) => {
        state.loading = false;
        state.apiKeys = action.payload;
      })
      .addCase(fetchApiKeys.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      })
      // Create API Key
      .addCase(createNewApiKey.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(createNewApiKey.fulfilled, (state, action: PayloadAction<ApiKeyCreatedResponse>) => {
        state.loading = false;
        // Don't store the raw api_key here since the list only stores ApiKeyResponse,
        // but we push it to list representation
        state.apiKeys.unshift(action.payload);
      })
      .addCase(createNewApiKey.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      })
      // Revoke API Key
      .addCase(revokeExistingApiKey.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(revokeExistingApiKey.fulfilled, (state, action: PayloadAction<string>) => {
        state.loading = false;
        state.apiKeys = state.apiKeys.filter((k) => k.id !== action.payload);
      })
      .addCase(revokeExistingApiKey.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      });
  },
});

export const { clearProjectError } = projectSlice.actions;
export default projectSlice.reducer;
