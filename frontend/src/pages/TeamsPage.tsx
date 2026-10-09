import { useCallback, useEffect, useState, type FormEvent } from 'react';
import PageHeader from '../components/PageHeader';
import Notice from '../components/Notice';
import EmptyState from '../components/EmptyState';
import api from '../services/api';
import { ENDPOINTS } from '../services/endpoints';
import { getErrorMessage, formatDate, listFromResponse } from '../lib/apiHelpers';
import type { Team } from '../types';

export default function TeamsPage() {
  const [teams, setTeams] = useState<Team[]>([]);
  const [name, setName] = useState('');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const loadTeams = useCallback(async () => {
    setLoading(true);
    try { const response = await api.get(ENDPOINTS.teams); setTeams(listFromResponse<Team>(response.data)); setError(''); }
    catch (caught) { setError(getErrorMessage(caught, 'Could not load teams.')); }
    finally { setLoading(false); }
  }, []);

  useEffect(() => { void loadTeams(); }, [loadTeams]);

  async function handleCreate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setSaving(true); setError(''); setSuccess('');
    try {
      await api.post(ENDPOINTS.teams, { name: name.trim() });
      setName(''); setSuccess('Team created.'); await loadTeams();
    } catch (caught) { setError(getErrorMessage(caught, 'Could not create the team. You may not have permission.')); }
    finally { setSaving(false); }
  }

  async function handleDelete(team: Team) {
    if (!window.confirm(`Delete the team “${team.name}”? This may affect its related data.`)) return;
    setError(''); setSuccess('');
    try { await api.delete(`${ENDPOINTS.teams}${team.id}/`); setTeams((current) => current.filter((item) => item.id !== team.id)); setSuccess('Team deleted.'); }
    catch (caught) { setError(getErrorMessage(caught, 'Could not delete the team. Only an authorized owner can do this.')); }
  }

  return <>
    <PageHeader title="Teams" description="Group people into workspaces and keep projects organized." />
    {(error || success) && <div className="mb-5"><Notice message={error || success} kind={error ? 'error' : 'success'} /></div>}
    <div className="grid gap-6 xl:grid-cols-[0.75fr_1.25fr]">
      <section className="h-fit rounded-2xl border border-slate-800 bg-slate-900/60 p-5 sm:p-6"><h2 className="font-semibold text-white">Create a team</h2><p className="mt-1 text-sm text-slate-400">Start with a clear team name.</p><form onSubmit={handleCreate} className="mt-5 space-y-4"><label className="block"><span className="mb-2 block text-sm text-slate-300">Team name</span><input required maxLength={120} value={name} onChange={(e) => setName(e.target.value)} placeholder="e.g. Backend Team" className="w-full rounded-xl border border-slate-700 bg-slate-950 px-4 py-3 text-sm text-white outline-none focus:border-cyan-300" /></label><button disabled={saving || !name.trim()} className="w-full rounded-xl bg-cyan-300 px-4 py-3 text-sm font-bold text-slate-950 hover:bg-cyan-200 disabled:opacity-50">{saving ? 'Creating…' : 'Create team'}</button></form><p className="mt-4 text-xs leading-5 text-slate-500">Team membership and ownership are handled by the Django API.</p></section>
      <section><div className="mb-3 flex items-center justify-between"><h2 className="font-semibold text-white">Available teams</h2><span className="rounded-full bg-slate-800 px-3 py-1 text-xs text-slate-300">{teams.length}</span></div>{loading ? <div className="rounded-2xl border border-slate-800 p-8 text-sm text-slate-500">Loading teams…</div> : teams.length === 0 ? <EmptyState title="No teams found" description="Create a team using the form. If creation is rejected, check the backend's validation or permissions." /> : <div className="grid gap-3 sm:grid-cols-2">{teams.map((team) => <article key={team.id} className="rounded-2xl border border-slate-800 bg-slate-900/50 p-5 transition hover:border-slate-700"><div className="flex items-start justify-between"><div className="grid size-10 place-items-center rounded-xl bg-violet-400/10 font-bold text-violet-300">{team.name.slice(0, 1).toUpperCase()}</div><button onClick={() => void handleDelete(team)} aria-label={`Delete ${team.name}`} className="rounded-lg px-2 py-1 text-xs text-slate-500 hover:bg-rose-400/10 hover:text-rose-300">Delete</button></div><h3 className="mt-4 font-semibold text-white">{team.name}</h3><p className="mt-1 text-xs text-slate-500">Team #{team.id}{team.created_at ? ` · Created ${formatDate(team.created_at)}` : ''}</p></article>)}</div>}</section>
    </div>
  </>;
}
