export interface RegisterRequest {
  email: string;
  password: string;
  organization_name?: string;
  role?: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  role: string;
  email: string;
  organization_id: string;
  organization_name: string;
}

export interface UserProfile {
  id: string;
  email: string;
  role: string;
  organization_id: string;
  organization_name: string;
}

export interface VerifyTokenRequest {
  token: string;
}

export interface VerifyTokenResponse {
  valid: boolean;
  user: UserProfile | null;
}

export interface RefreshTokenRequest {
  refresh_token: string;
}
