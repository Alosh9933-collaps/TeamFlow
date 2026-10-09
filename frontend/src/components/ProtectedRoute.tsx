import { Navigate } from 'react-router-dom';
import type { ReactNode } from 'react';
import { useAuth } from '../context/AuthContext';

export default function ProtectedRoute({ children }: { children: ReactNode }) {
  const { user, isLoading } = useAuth();
  if (isLoading) {
    return <div className="grid min-h-screen place-items-center bg-slate-950 text-slate-300">Loading TeamFlow…</div>;
  }
  if (!user) return <Navigate to="/login" replace />;
  return children;
}
