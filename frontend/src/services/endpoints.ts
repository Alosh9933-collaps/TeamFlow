// Keep API paths in one place. If a Django URL differs, change it here.
export const ENDPOINTS = {
  auth: {
    login: 'auth/token/',
    refresh: 'auth/token/refresh/',
    me: 'auth/me/',
    // Assumed from the RegisterView name in the backend project.
    register: 'auth/register/',
  },
  teams: 'teams/',
  projects: 'projects/',
  tasks: 'tasks/',
  notifications: 'notifications/',
  // These two routes may need alignment with apps/notifications/urls.py.
  notificationRead: (id: number) => `notifications/${id}/read/`,
  notificationReadAll: 'notifications/read-all/',
  projectActivity: (projectId: number) => `projects/${projectId}/activity/`,
} as const;
