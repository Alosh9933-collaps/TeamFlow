import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from 'react';
import api from '../services/api';
import { ENDPOINTS } from '../services/endpoints';
import type { User } from '../types';

 type Credentials = { username: string; password: string };
 type RegistrationData = { username: string; email: string; password: string; password_confirm: string };

type AuthContextValue = {
  user: User | null;
  isLoading: boolean;
  login: (credentials: Credentials) => Promise<void>;
  register: (payload: RegistrationData) => Promise<void>;
  logout: () => void;
  reloadUser: () => Promise<void>;
};

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(Boolean(localStorage.getItem('access_token')));

  const logout = useCallback(() => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    setUser(null);
  }, []);

  const reloadUser = useCallback(async () => {
    if (!localStorage.getItem('access_token')) {
      setUser(null);
      setIsLoading(false);
      return;
    }
    try {
      const response = await api.get<User>(ENDPOINTS.auth.me);
      setUser(response.data);
    } catch {
      logout();
    } finally {
      setIsLoading(false);
    }
  }, [logout]);

  useEffect(() => {
    void reloadUser();
    const handleUnauthorized = () => {
      setUser(null);
      setIsLoading(false);
    };
    window.addEventListener('teamflow:unauthorized', handleUnauthorized);
    return () => window.removeEventListener('teamflow:unauthorized', handleUnauthorized);
  }, [reloadUser]);

  const login = useCallback(async ({ username, password }: Credentials) => {
    const response = await api.post(ENDPOINTS.auth.login, { username, password });
    localStorage.setItem('access_token', response.data.access as string);
    localStorage.setItem('refresh_token', response.data.refresh as string);
    await reloadUser();
    if (!localStorage.getItem('access_token')) {
      throw new Error('Login succeeded but the current-user endpoint could not be loaded. Check the auth/me URL.');
    }
  }, [reloadUser]);

  const register = useCallback(async (payload: RegistrationData) => {
    await api.post(ENDPOINTS.auth.register, payload);
  }, []);

  const value = useMemo(() => ({ user, isLoading, login, register, logout, reloadUser }), [user, isLoading, login, register, logout, reloadUser]);
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth must be used inside AuthProvider');
  return context;
}
