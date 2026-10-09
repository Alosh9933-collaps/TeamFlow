import { useState, type FormEvent } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { getErrorMessage } from '../lib/apiHelpers';
import Notice from '../components/Notice';

export default function RegisterPage() {
  const { register } = useAuth();
  const navigate = useNavigate();
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError('');
    if (password !== confirmPassword) {
      setError('Passwords do not match.');
      return;
    }
    setSubmitting(true);
    try {
      await register({ username, email, password, password_confirm: confirmPassword });
      navigate('/login', { replace: true, state: { message: 'Account created. Sign in to continue.' } });
    } catch (caught) {
      setError(getErrorMessage(caught, 'Registration failed. Check the fields and try again.'));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="grid min-h-screen place-items-center bg-slate-950 px-5 py-12">
      <div className="w-full max-w-lg rounded-3xl border border-slate-800 bg-slate-900/70 p-7 shadow-2xl shadow-black/20 sm:p-10">
        <Link to="/login" className="text-sm font-semibold text-cyan-300 hover:text-cyan-200">← Back to sign in</Link>
        <div className="mt-8 flex items-center gap-3"><div className="grid size-10 place-items-center rounded-xl bg-cyan-300 font-black text-slate-950">TF</div><span className="text-lg font-bold text-white">TeamFlow</span></div>
        <h1 className="mt-8 text-3xl font-bold text-white">Create your account</h1><p className="mt-2 text-sm leading-6 text-slate-400">Set up your workspace identity to get started.</p>
        <form onSubmit={handleSubmit} className="mt-7 space-y-4">
          {error && <Notice message={error} />}
          <label className="block"><span className="mb-2 block text-sm font-medium text-slate-300">Username</span><input required minLength={3} autoComplete="username" value={username} onChange={(e) => setUsername(e.target.value)} className="w-full rounded-xl border border-slate-700 bg-slate-950 px-4 py-3 text-sm text-white outline-none focus:border-cyan-300" /></label>
          <label className="block"><span className="mb-2 block text-sm font-medium text-slate-300">Email</span><input required type="email" autoComplete="email" value={email} onChange={(e) => setEmail(e.target.value)} className="w-full rounded-xl border border-slate-700 bg-slate-950 px-4 py-3 text-sm text-white outline-none focus:border-cyan-300" /></label>
          <div className="grid gap-4 sm:grid-cols-2"><label className="block"><span className="mb-2 block text-sm font-medium text-slate-300">Password</span><input required minLength={8} type="password" autoComplete="new-password" value={password} onChange={(e) => setPassword(e.target.value)} className="w-full rounded-xl border border-slate-700 bg-slate-950 px-4 py-3 text-sm text-white outline-none focus:border-cyan-300" /></label><label className="block"><span className="mb-2 block text-sm font-medium text-slate-300">Confirm password</span><input required type="password" autoComplete="new-password" value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)} className="w-full rounded-xl border border-slate-700 bg-slate-950 px-4 py-3 text-sm text-white outline-none focus:border-cyan-300" /></label></div>
          <button disabled={submitting} className="mt-2 w-full rounded-xl bg-cyan-300 px-4 py-3.5 text-sm font-bold text-slate-950 transition hover:bg-cyan-200 disabled:opacity-60">{submitting ? 'Creating account…' : 'Create account'}</button>
        </form>
        <p className="mt-6 text-xs leading-5 text-slate-500">Registration fields and URL must match the RegisterSerializer configured in Django.</p>
      </div>
    </div>
  );
}
