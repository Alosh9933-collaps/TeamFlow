import { Link } from 'react-router-dom';

export default function NotFoundPage() {
  return <div className="grid min-h-screen place-items-center bg-slate-950 px-5 text-center text-white"><div><p className="text-xs font-bold uppercase tracking-[0.25em] text-cyan-300">404 · Not found</p><h1 className="mt-4 text-4xl font-bold">This page does not exist.</h1><p className="mt-3 text-slate-400">The route may have moved or the URL may be incorrect.</p><Link to="/dashboard" className="mt-7 inline-flex rounded-xl bg-cyan-300 px-4 py-3 text-sm font-bold text-slate-950">Back to dashboard</Link></div></div>;
}
