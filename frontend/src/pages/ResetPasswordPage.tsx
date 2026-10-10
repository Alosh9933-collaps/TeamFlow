import { useState, type FormEvent } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import api from '../services/api';
import { ENDPOINTS } from '../services/endpoints';
import { getErrorMessage } from '../lib/apiHelpers';
import Notice from '../components/Notice';

export default function ResetPasswordPage() {
  const { uidb64, token } = useParams<{ uidb64: string; token: string }>();
  const navigate = useNavigate();
  const [password, setPassword] = useState('');
  const [passwordConfirm, setPasswordConfirm] = useState('');
  const [error, setError] = useState('');
  const [complete, setComplete] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError('');

    if (!uidb64 || !token) {
      setError('This password reset link is incomplete. Request a new one.');
      return;
    }

    if (password !== passwordConfirm) {
      setError('The passwords do not match.');
      return;
    }

    setSubmitting(true);
    try {
      await api.post(
        ENDPOINTS.auth.passwordResetConfirm(uidb64, token),
        {
          password,
          password_confirm: passwordConfirm,
        },
      );
      setComplete(true);
    } catch (caught) {
      setError(
        getErrorMessage(
          caught,
          'This reset link may be invalid or expired. Request a new link and try again.',
        ),
      );
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="grid min-h-screen bg-slate-950 lg:grid-cols-[1.05fr_0.95fr]">
      <section className="relative hidden overflow-hidden border-r border-slate-800 lg:flex lg:flex-col lg:justify-between lg:p-14">
        <div className="absolute -left-24 top-28 size-80 rounded-full bg-cyan-400/10 blur-3xl" />
        <Link to="/login" className="relative flex items-center gap-3">
          <div className="grid size-11 place-items-center rounded-xl bg-cyan-300 font-black text-slate-950">TF</div>
          <span className="text-lg font-bold text-white">TeamFlow</span>
        </Link>
        <div className="relative max-w-xl py-14">
          <p className="mb-5 text-xs font-bold uppercase tracking-[0.25em] text-cyan-300">Secure account recovery</p>
          <h1 className="text-5xl font-bold leading-[1.12] tracking-tight text-white xl:text-6xl">
            A fresh start for <span className="text-cyan-300">your password.</span>
          </h1>
          <p className="mt-6 max-w-lg text-base leading-7 text-slate-400">
            Choose a strong password that you haven’t used for this account before.
          </p>
        </div>
        <p className="relative text-xs text-slate-600">Your workspace, organized.</p>
      </section>

      <section className="flex items-center justify-center px-5 py-12 sm:px-8">
        <div className="w-full max-w-md">
          <div className="mb-10 flex items-center gap-3 lg:hidden">
            <div className="grid size-10 place-items-center rounded-xl bg-cyan-300 font-black text-slate-950">TF</div>
            <span className="text-lg font-bold text-white">TeamFlow</span>
          </div>

          {complete ? (
            <div>
              <p className="text-sm font-semibold text-emerald-300">Password updated</p>
              <h2 className="mt-2 text-3xl font-bold tracking-tight text-white">You’re all set.</h2>
              <p className="mt-3 text-sm leading-6 text-slate-400">
                Your password has been reset. Sign in with your new password to continue.
              </p>
              <button
                onClick={() => navigate('/login', { replace: true })}
                className="mt-8 flex w-full items-center justify-center rounded-xl bg-cyan-300 px-4 py-3.5 text-sm font-bold text-slate-950 transition hover:bg-cyan-200"
              >
                Back to sign in
              </button>
            </div>
          ) : (
            <>
              <p className="text-sm font-semibold text-cyan-300">Create a new password</p>
              <h2 className="mt-2 text-3xl font-bold tracking-tight text-white">Reset your password</h2>
              <p className="mt-3 text-sm leading-6 text-slate-400">
                Enter your new password twice to confirm it.
              </p>

              <form onSubmit={handleSubmit} className="mt-8 space-y-5">
                {error && <Notice message={error} />}
                <label className="block">
                  <span className="mb-2 block text-sm font-medium text-slate-300">New password</span>
                  <input
                    type="password"
                    autoComplete="new-password"
                    required
                    minLength={8}
                    value={password}
                    onChange={(event) => setPassword(event.target.value)}
                    className="w-full rounded-xl border border-slate-700 bg-slate-900 px-4 py-3 text-sm text-white outline-none transition placeholder:text-slate-600 focus:border-cyan-300 focus:ring-2 focus:ring-cyan-300/10"
                    placeholder="Enter a new password"
                  />
                </label>
                <label className="block">
                  <span className="mb-2 block text-sm font-medium text-slate-300">Confirm new password</span>
                  <input
                    type="password"
                    autoComplete="new-password"
                    required
                    minLength={8}
                    value={passwordConfirm}
                    onChange={(event) => setPasswordConfirm(event.target.value)}
                    className="w-full rounded-xl border border-slate-700 bg-slate-900 px-4 py-3 text-sm text-white outline-none transition placeholder:text-slate-600 focus:border-cyan-300 focus:ring-2 focus:ring-cyan-300/10"
                    placeholder="Repeat the new password"
                  />
                </label>
                <button
                  disabled={submitting}
                  className="flex w-full items-center justify-center rounded-xl bg-cyan-300 px-4 py-3.5 text-sm font-bold text-slate-950 transition hover:bg-cyan-200 disabled:cursor-wait disabled:opacity-60"
                >
                  {submitting ? 'Updating…' : 'Set new password'}
                </button>
              </form>

              <p className="mt-7 text-center text-sm text-slate-400">
                Need a new reset link?{' '}
                <Link to="/forgot-password" className="font-semibold text-cyan-300 hover:text-cyan-200">Request another</Link>
              </p>
            </>
          )}
        </div>
      </section>
    </div>
  );
}
