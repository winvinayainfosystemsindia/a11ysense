export interface ProjectCreate {
  name: string;
  project_type?: 'web_page' | 'web_application';
  base_url?: string;
}

export interface ProjectResponse {
  id: string;
  name: string;
  project_type?: 'web_page' | 'web_application';
  base_url?: string;
  organization_id: string;
  created_at: string;
}
