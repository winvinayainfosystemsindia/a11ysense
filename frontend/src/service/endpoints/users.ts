import api from '../api';
import type { UserResponse, UserCreateRequest, UserUpdateRequest, OrganizationResponse } from '../../model/users.model';

export const userService = {
  listUsers: async (): Promise<UserResponse[]> => {
    const response = await api.get<UserResponse[]>('/api/users');
    return response.data;
  },

  createUser: async (req: UserCreateRequest): Promise<UserResponse> => {
    const response = await api.post<UserResponse>('/api/users', req);
    return response.data;
  },

  updateUser: async (id: string, req: UserUpdateRequest): Promise<UserResponse> => {
    const response = await api.put<UserResponse>(`/api/users/${id}`, req);
    return response.data;
  },

  deleteUser: async (id: string): Promise<void> => {
    await api.delete(`/api/users/${id}`);
  },

  listOrganizations: async (): Promise<OrganizationResponse[]> => {
    const response = await api.get<OrganizationResponse[]>('/api/organizations');
    return response.data;
  }
};
