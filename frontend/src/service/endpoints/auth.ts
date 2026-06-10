import api from '../api';
import type {
  RegisterRequest,
  LoginRequest,
  TokenResponse,
  UserProfile,
  VerifyTokenRequest,
  VerifyTokenResponse,
  RefreshTokenRequest,
} from '../../model/auth.model';

export const authService = {
  register: async (req: RegisterRequest): Promise<UserProfile> => {
    const response = await api.post<UserProfile>('/auth/register', req);
    return response.data;
  },

  login: async (req: LoginRequest): Promise<TokenResponse> => {
    const response = await api.post<TokenResponse>('/auth/login', req);
    return response.data;
  },

  getProfile: async (): Promise<UserProfile> => {
    const response = await api.get<UserProfile>('/auth/me');
    return response.data;
  },

  verifyToken: async (req: VerifyTokenRequest): Promise<VerifyTokenResponse> => {
    const response = await api.post<VerifyTokenResponse>('/auth/verify', req);
    return response.data;
  },

  refreshToken: async (req: RefreshTokenRequest): Promise<TokenResponse> => {
    const response = await api.post<TokenResponse>('/auth/refresh', req);
    return response.data;
  },
};
