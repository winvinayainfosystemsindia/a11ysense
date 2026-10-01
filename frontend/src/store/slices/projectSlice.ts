import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import type { PayloadAction } from '@reduxjs/toolkit';
import { projectService } from '../../service/endpoints/projects';
import type { ProjectResponse, ProjectCreate } from '../../model/project.model';

interface ProjectState {
  projects: ProjectResponse[];
  loading: boolean;
  error: string | null;
}

const initialState: ProjectState = {
  projects: [],
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
  async (payload: string | ProjectCreate, { rejectWithValue }) => {
    try {
      return await projectService.createProject(payload);
    } catch (err: any) {
      return rejectWithValue(err.userMessage || 'Failed to create project');
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
      });
  },
});

export const { clearProjectError } = projectSlice.actions;
export default projectSlice.reducer;
