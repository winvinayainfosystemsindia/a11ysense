export interface ProjectCreate {
  name: string;
}

export interface ProjectResponse {
  id: string;
  name: string;
  organization_id: string;
  created_at: string;
}

export interface ApiKeyCreate {
  name: string;
  expires_in_days?: number;
}

export interface ApiKeyResponse {
  id: string;
  name: string;
  created_at: string;
  expires_at?: string;
}

export interface ApiKeyCreatedResponse extends ApiKeyResponse {
  api_key: string;
}
