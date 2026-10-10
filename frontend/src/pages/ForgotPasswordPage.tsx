import { useState, type FormEvent } from 'react';
import { Link } from 'react-router-dom';
import api from '../services/api';
import { ENDPOINTS } from '../services/endpoints';
import { getErrorMessage } from '../lib/apiHelpers';
import Notice from '../components/Notice';

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState('');
  const [error, setError] = useState('');
  const [sent, setSent] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError('');
    setSent(false);
    setSubmitting(true);

    try {
      await api.post(ENDPOINTS.auth.passwordResetRequest, {
        email: email.trim(),
      });
      // The API intentionally returns the same response whether or not
      // the account exists, to avoid exposing registered email addresses.
      setSent(true);
    } catch (caught) {
      setError(
        getErrorMessage(
          caught,
          'We could not process your request. Please try again.',
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
          <p className="mb-5 text-xs font-bold uppercase tracking-[0.25em] text-cyan-300">Account recovery</p>
          <h1 className="text-5xl font-bold leading-[1.12] tracking-tight text-white xl:text-6xl">
            Get back to <span className="text-cyan-300">your flow.</span>
          </h1>
          <p className="mt-6 max-w-lg text-base leading-7 text-slate-400">
            We’ll help you securely reset your password and get back to your workspace.
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
          <p className="text-sm font-semibold text-cyan-300">Forgot your password?</p>
          <h2 className="mt-2 text-3xl font-bold tracking-tight text-white">Reset your password</h2>
          <p className="mt-3 text-sm leading-6 text-slate-400">
            Enter the email address associated with your account. If an active account matches, we’ll send a reset link.
          </p>

          <form onSubmit={handleSubmit} className="mt-8 space-y-5">
            {error && <Notice message={error} />}
            {sent && (
              <div role="status" className="rounded-xl border border-emerald-800 bg-emerald-950/60 px-4 py-3 text-sm leading-6 text-emerald-200">
                If an active account exists for that email, a password reset link will be sent. Check your inbox.
              </div>
            )}
            <label className="block">
              <span className="mb-2 block text-sm font-medium text-slate-300">Email address</span>
              <input
                type="email"
                autoComplete="email"
                required
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                className="w-full rounded-xl border border-slate-700 bg-slate-900 px-4 py-3 text-sm text-white outline-none transition placeholder:text-slate-600 focus:border-cyan-300 focus:ring-2 focus:ring-cyan-300/10"
                placeholder="you@example.com"
              />
            </label>
            <button
              disabled={submitting}
              className="flex w-full items-center justify-center rounded-xl bg-cyan-300 px-4 py-3.5 text-sm font-bold text-slate-950 transition hover:bg-cyan-200 disabled:cursor-wait disabled:opacity-60"
            >
              {submitting ? 'Sending…' : 'Send reset link'}
            </button>
          </form>

          <p className="mt-7 text-center text-sm text-slate-400">
            Remembered your password?{' '}
            <Link to="/login" className="font-semibold text-cyan-300 hover:text-cyan-200">Back to sign in</Link>
          </p>
        </div>
      </section>
    </div>
  );
}
