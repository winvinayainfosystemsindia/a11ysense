import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import type { PayloadAction } from '@reduxjs/toolkit';
import { authService } from '../../service/endpoints/auth';
import type {
  RegisterRequest,
  LoginRequest,
  TokenResponse,
  UserProfile,
  VerifyTokenRequest,
  RefreshTokenRequest
} from '../../model/auth.model';

interface AuthState {
  user: UserProfile | null;
  token: string | null;
  isAuthenticated: boolean;
  loading: boolean;
  error: string | null;
}

const initialState: AuthState = {
  user: null,
  token: localStorage.getItem('auth_token'),
  isAuthenticated: !!localStorage.getItem('auth_token'),
  loading: false,
  error: null,
};

export const registerUser = createAsyncThunk(
  'auth/register',
  async (req: RegisterRequest, { rejectWithValue }) => {
    try {
      return await authService.register(req);
    } catch (err: any) {
      return rejectWithValue(err.userMessage || 'Registration failed');
    }
  }
);

export const loginUser = createAsyncThunk(
  'auth/login',
  async (req: LoginRequest, { rejectWithValue }) => {
    try {
      const data = await authService.login(req);
      const email = data.user?.email || data.email || '';
      const role = data.user?.role || data.role || '';
      const orgName = data.user?.organization_name || data.organization_name || '';
      const orgId = data.user?.organization_id || data.organization_id || '';

      localStorage.setItem('auth_token', data.access_token);
      localStorage.setItem('refresh_token', data.refresh_token);
      if (email) localStorage.setItem('user_email', email);
      if (role) localStorage.setItem('user_role', role);
      if (orgName) localStorage.setItem('org_name', orgName);
      if (orgId) localStorage.setItem('org_id', orgId);
      return data;
    } catch (err: any) {
      return rejectWithValue(err.userMessage || 'Incorrect email or password');
    }
  }
);

export const getUserProfile = createAsyncThunk(
  'auth/getProfile',
  async (_, { rejectWithValue }) => {
    try {
      return await authService.getProfile();
    } catch (err: any) {
      return rejectWithValue(err.userMessage || 'Failed to retrieve profile');
    }
  }
);

export const verifyUserToken = createAsyncThunk(
  'auth/verifyToken',
  async (req: VerifyTokenRequest, { rejectWithValue }) => {
    try {
      return await authService.verifyToken(req);
    } catch (err: any) {
      return rejectWithValue(err.userMessage || 'Token verification failed');
    }
  }
);

export const refreshUserToken = createAsyncThunk(
  'auth/refreshToken',
  async (req: RefreshTokenRequest, { rejectWithValue }) => {
    try {
      const data = await authService.refreshToken(req);
      const email = data.user?.email || data.email || '';
      const role = data.user?.role || data.role || '';
      const orgName = data.user?.organization_name || data.organization_name || '';
      const orgId = data.user?.organization_id || data.organization_id || '';

      localStorage.setItem('auth_token', data.access_token);
      localStorage.setItem('refresh_token', data.refresh_token);
      if (email) localStorage.setItem('user_email', email);
      if (role) localStorage.setItem('user_role', role);
      if (orgName) localStorage.setItem('org_name', orgName);
      if (orgId) localStorage.setItem('org_id', orgId);
      return data;
    } catch (err: any) {
      return rejectWithValue(err.userMessage || 'Token refresh failed');
    }
  }
);

const authSlice = createSlice({
  name: 'auth',
  initialState,
  reducers: {
    logoutUser(state) {
      state.user = null;
      state.token = null;
      state.isAuthenticated = false;
      state.error = null;
      localStorage.removeItem('auth_token');
      localStorage.removeItem('refresh_token');
      localStorage.removeItem('user_email');
      localStorage.removeItem('user_role');
      localStorage.removeItem('org_name');
    },
    clearAuthError(state) {
      state.error = null;
    }
  },
  extraReducers: (builder) => {
    builder
      // Register
      .addCase(registerUser.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(registerUser.fulfilled, (state) => {
        state.loading = false;
      })
      .addCase(registerUser.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      })
      // Login
      .addCase(loginUser.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(loginUser.fulfilled, (state, action: PayloadAction<TokenResponse>) => {
        state.loading = false;
        state.token = action.payload.access_token;
        state.isAuthenticated = true;
        const email = action.payload.user?.email || action.payload.email || '';
        const role = action.payload.user?.role || action.payload.role || 'Admin';
        const orgId = action.payload.user?.organization_id || action.payload.organization_id || '';
        const orgName = action.payload.user?.organization_name || action.payload.organization_name || 'Enterprise';
        const userId = action.payload.user?.id || '';

        state.user = {
          id: userId,
          email,
          role,
          organization_id: orgId,
          organization_name: orgName,
        };
      })
      .addCase(loginUser.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      })
      // Profile
      .addCase(getUserProfile.pending, (state) => {
        state.loading = true;
      })
      .addCase(getUserProfile.fulfilled, (state, action: PayloadAction<UserProfile>) => {
        state.loading = false;
        state.user = action.payload;
        if (action.payload.email) localStorage.setItem('user_email', action.payload.email);
        if (action.payload.role) localStorage.setItem('user_role', action.payload.role);
        if (action.payload.organization_name) localStorage.setItem('org_name', action.payload.organization_name);
        if (action.payload.organization_id) localStorage.setItem('org_id', action.payload.organization_id);
      })
      .addCase(getUserProfile.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      })
      // Verify Token
      .addCase(verifyUserToken.fulfilled, (state, action) => {
        if (action.payload.valid && action.payload.user) {
          state.user = action.payload.user;
          state.isAuthenticated = true;
          if (action.payload.user.email) localStorage.setItem('user_email', action.payload.user.email);
          if (action.payload.user.role) localStorage.setItem('user_role', action.payload.user.role);
          if (action.payload.user.organization_name) localStorage.setItem('org_name', action.payload.user.organization_name);
          if (action.payload.user.organization_id) localStorage.setItem('org_id', action.payload.user.organization_id);
        } else {
          state.user = null;
          state.isAuthenticated = false;
          state.token = null;
          localStorage.removeItem('auth_token');
        }
      })
      // Refresh Token
      .addCase(refreshUserToken.fulfilled, (state, action: PayloadAction<TokenResponse>) => {
        state.token = action.payload.access_token;
        state.isAuthenticated = true;
        const email = action.payload.user?.email || action.payload.email || '';
        const role = action.payload.user?.role || action.payload.role || 'Admin';
        const orgId = action.payload.user?.organization_id || action.payload.organization_id || '';
        const orgName = action.payload.user?.organization_name || action.payload.organization_name || 'Enterprise';
        const userId = action.payload.user?.id || '';

        state.user = {
          id: userId,
          email,
          role,
          organization_id: orgId,
          organization_name: orgName,
        };
      })
      .addCase(refreshUserToken.rejected, (state) => {
        state.user = null;
        state.isAuthenticated = false;
        state.token = null;
        localStorage.removeItem('auth_token');
        localStorage.removeItem('refresh_token');
      });
  },
});

export const { logoutUser, clearAuthError } = authSlice.actions;
export default authSlice.reducer;
