export type User = {
  id: number;
  username: string;
  email: string;
};

export type Team = {
  id: number;
  name: string;
  created_at?: string;
};

export type Project = {
  id: number;
  name: string;
  description?: string;
  team: number | Pick<Team, 'id' | 'name'>;
  created_at?: string;
};

export type Task = {
  id: number;
  title: string;
  description?: string;
  status: string;
  priority: string;
  project: number | Pick<Project, 'id' | 'name'>;
  due_date?: string | null;
  created_at?: string;
};

export type NotificationItem = {
  id: number;
  notification_type?: string;
  message?: string;
  detail?: string;
  metadata?: Record<string, unknown>;
  read_at?: string | null;
  created_at?: string;
  actor_username?: string | null;
};

export type ActivityItem = {
  id: number;
  action: string;
  actor_username?: string | null;
  target_type?: string;
  metadata?: Record<string, unknown>;
  created_at?: string;
};

export type PaginatedResponse<T> = {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
};
