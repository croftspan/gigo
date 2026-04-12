export type TaskStatus = 'draft' | 'active' | 'paused' | 'completed' | 'archived';

export interface Task {
  id: string;
  title: string;
  description: string;
  status: TaskStatus;
  project_id: string;
  assignee_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface Project {
  id: string;
  name: string;
  description: string;
  memberCount: number;
  status: 'creating' | 'ready' | 'archived';
  created_at: string;
}

export interface ApiResponse<T> {
  data: T;
  total: number;
}

export interface PaginationParams {
  page: number;
  limit: number;
}
