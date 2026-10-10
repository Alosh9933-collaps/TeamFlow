import { useState, type FormEvent } from 'react';
import { Link, Navigate, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { getErrorMessage } from '../lib/apiHelpers';
import Notice from '../components/Notice';

export default function LoginPage() {
  const { login, user, isLoading } = useAuth();
  const navigate = useNavigate();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  if (!isLoading && user) return <Navigate to="/dashboard" replace />;

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError('');
    setSubmitting(true);
    try {
      await login({ username, password });
      navigate('/dashboard', { replace: true });
    } catch (caught) {
      setError(getErrorMessage(caught, 'Login failed. Check your credentials.'));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="grid min-h-screen bg-slate-950 lg:grid-cols-[1.05fr_0.95fr]">
      <section className="relative hidden overflow-hidden border-r border-slate-800 lg:flex lg:flex-col lg:justify-between lg:p-14">
        <div className="absolute -left-24 top-28 size-80 rounded-full bg-cyan-400/10 blur-3xl" />
        <div className="relative flex items-center gap-3"><div className="grid size-11 place-items-center rounded-xl bg-cyan-300 font-black text-slate-950">TF</div><span className="text-lg font-bold text-white">TeamFlow</span></div>
        <div className="relative max-w-xl py-14"><p className="mb-5 text-xs font-bold uppercase tracking-[0.25em] text-cyan-300">Bring your work together</p><h1 className="text-5xl font-bold leading-[1.12] tracking-tight text-white xl:text-6xl">Less chasing.<br /><span className="text-cyan-300">More getting done.</span></h1><p className="mt-6 max-w-lg text-base leading-7 text-slate-400">A clearer way to coordinate teams, keep projects moving, and turn tasks into progress.</p><div className="mt-10 grid max-w-md grid-cols-3 gap-3">{[['01','Teams'],['02','Projects'],['03','Tasks']].map(([number, label]) => <div key={number} className="rounded-2xl border border-slate-800 bg-slate-900/60 p-4"><p className="text-xs text-cyan-300">{number}</p><p className="mt-2 text-sm font-semibold text-slate-200">{label}</p></div>)}</div></div>
        <p className="relative text-xs text-slate-600">Your workspace, organized.</p>
      </section>
      <section className="flex items-center justify-center px-5 py-12 sm:px-8">
        <div className="w-full max-w-md">
          <div className="mb-10 flex items-center gap-3 lg:hidden"><div className="grid size-10 place-items-center rounded-xl bg-cyan-300 font-black text-slate-950">TF</div><span className="text-lg font-bold text-white">TeamFlow</span></div>
          <p className="text-sm font-semibold text-cyan-300">Welcome back</p><h2 className="mt-2 text-3xl font-bold tracking-tight text-white">Sign in to your account</h2><p className="mt-3 text-sm leading-6 text-slate-400">Use your TeamFlow credentials to continue.</p>
          <form onSubmit={handleSubmit} className="mt-8 space-y-5">
            {error && <Notice message={error} />}
            <label className="block"><span className="mb-2 block text-sm font-medium text-slate-300">Username</span><input autoComplete="username" required value={username} onChange={(e) => setUsername(e.target.value)} className="w-full rounded-xl border border-slate-700 bg-slate-900 px-4 py-3 text-sm text-white outline-none transition placeholder:text-slate-600 focus:border-cyan-300 focus:ring-2 focus:ring-cyan-300/10" placeholder="Your username" /></label>
            <label className="block"><span className="mb-2 block text-sm font-medium text-slate-300">Password</span><input type="password" autoComplete="current-password" required value={password} onChange={(e) => setPassword(e.target.value)} className="w-full rounded-xl border border-slate-700 bg-slate-900 px-4 py-3 text-sm text-white outline-none transition placeholder:text-slate-600 focus:border-cyan-300 focus:ring-2 focus:ring-cyan-300/10" placeholder="Your password" /></label>
            <button disabled={submitting} className="flex w-full items-center justify-center rounded-xl bg-cyan-300 px-4 py-3.5 text-sm font-bold text-slate-950 transition hover:bg-cyan-200 disabled:cursor-wait disabled:opacity-60">{submitting ? 'Signing in…' : 'Sign in'}</button>
          </form>
          <p className="mt-4 text-right text-sm">
            <Link to="/forgot-password" className="font-semibold text-cyan-300 hover:text-cyan-200">Forgot password?</Link>
          </p>
          <p className="mt-7 text-center text-sm text-slate-400">New to TeamFlow? <Link to="/register" className="font-semibold text-cyan-300 hover:text-cyan-200">Create an account</Link></p>
          <p className="mt-10 text-center text-xs text-slate-600">Connected to your Django REST API</p>
        </div>
      </section>
    </div>
  );
}
