export interface UserResponse {
  id: string;
  email: string;
  role: string;
  organization_id: string;
  organization_name: string;
  created_at: string;
}

export interface UserCreateRequest {
  email: string;
  password?: string;
  role: string;
  organization_id?: string;
}

export interface UserUpdateRequest {
  email?: string;
  role?: string;
  organization_id?: string;
}

export interface OrganizationResponse {
  id: string;
  name: string;
}
