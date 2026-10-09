import { useCallback, useEffect, useState, type FormEvent } from 'react';
import { Link } from 'react-router-dom';
import PageHeader from '../components/PageHeader';
import Notice from '../components/Notice';
import EmptyState from '../components/EmptyState';
import api from '../services/api';
import { ENDPOINTS } from '../services/endpoints';
import { getErrorMessage, listFromResponse } from '../lib/apiHelpers';
import type { Project, Team } from '../types';

export default function ProjectsPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [teams, setTeams] = useState<Team[]>([]);
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [teamId, setTeamId] = useState('');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const load = useCallback(async () => {
    setLoading(true);
    const [projectResult, teamResult] = await Promise.allSettled([api.get(ENDPOINTS.projects), api.get(ENDPOINTS.teams)]);
    if (projectResult.status === 'fulfilled') setProjects(listFromResponse<Project>(projectResult.value.data));
    else setError(getErrorMessage(projectResult.reason, 'Could not load projects.'));
    if (teamResult.status === 'fulfilled') {
      const loadedTeams = listFromResponse<Team>(teamResult.value.data);
      setTeams(loadedTeams);
      if (!teamId && loadedTeams.length) setTeamId(String(loadedTeams[0].id));
    }
    setLoading(false);
  }, [teamId]);

  useEffect(() => { void load(); }, [load]);

  async function handleCreate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setSaving(true); setError(''); setSuccess('');
    try {
      await api.post(ENDPOINTS.projects, { team: Number(teamId), name: name.trim(), description: description.trim() });
      setName(''); setDescription(''); setSuccess('Project created.'); await load();
    } catch (caught) { setError(getErrorMessage(caught, 'Could not create project. Team owners/admins may be the only roles allowed.')); }
    finally { setSaving(false); }
  }

  function getTeamName(project: Project) {
    if (typeof project.team !== 'number') return project.team?.name || 'Team';
    return teams.find((team) => team.id === project.team)?.name || `Team #${project.team}`;
  }

  return <>
    <PageHeader title="Projects" description="Track a project from kickoff to completion. Open any project to see its work." />
    {(error || success) && <div className="mb-5"><Notice message={error || success} kind={error ? 'error' : 'success'} /></div>}
    <div className="grid gap-6 xl:grid-cols-[0.8fr_1.2fr]">
      <section className="h-fit rounded-2xl border border-slate-800 bg-slate-900/60 p-5 sm:p-6"><h2 className="font-semibold text-white">New project</h2><p className="mt-1 text-sm text-slate-400">Choose a team and add project details.</p>
        {teams.length === 0 && !loading && <div className="mt-4"><Notice message="Create or join a team before creating a project." kind="info" /></div>}
        <form onSubmit={handleCreate} className="mt-5 space-y-4"><label className="block"><span className="mb-2 block text-sm text-slate-300">Team</span><select required value={teamId} onChange={(e) => setTeamId(e.target.value)} className="w-full rounded-xl border border-slate-700 bg-slate-950 px-4 py-3 text-sm text-white outline-none focus:border-cyan-300"><option value="">Select a team</option>{teams.map((team) => <option key={team.id} value={team.id}>{team.name}</option>)}</select></label><label className="block"><span className="mb-2 block text-sm text-slate-300">Project name</span><input required value={name} onChange={(e) => setName(e.target.value)} placeholder="e.g. TeamFlow web app" className="w-full rounded-xl border border-slate-700 bg-slate-950 px-4 py-3 text-sm text-white outline-none focus:border-cyan-300" /></label><label className="block"><span className="mb-2 block text-sm text-slate-300">Description</span><textarea rows={3} value={description} onChange={(e) => setDescription(e.target.value)} placeholder="What is this project about?" className="w-full resize-y rounded-xl border border-slate-700 bg-slate-950 px-4 py-3 text-sm text-white outline-none focus:border-cyan-300" /></label><button disabled={saving || !teamId || !name.trim()} className="w-full rounded-xl bg-cyan-300 px-4 py-3 text-sm font-bold text-slate-950 hover:bg-cyan-200 disabled:opacity-50">{saving ? 'Creating…' : 'Create project'}</button></form>
      </section>
      <section><div className="mb-3 flex items-center justify-between"><h2 className="font-semibold text-white">Projects you can access</h2><span className="rounded-full bg-slate-800 px-3 py-1 text-xs text-slate-300">{projects.length}</span></div>{loading ? <div className="rounded-2xl border border-slate-800 p-8 text-sm text-slate-500">Loading projects…</div> : projects.length === 0 ? <EmptyState title="Your projects will show up here" description="Create one using the form. If you do not have the right team role, Django will reject the request." /> : <div className="grid gap-4 md:grid-cols-2">{projects.map((project) => <article key={project.id} className="group rounded-2xl border border-slate-800 bg-slate-900/50 p-5 transition hover:-translate-y-0.5 hover:border-cyan-400/30"><div className="flex items-start justify-between gap-3"><div className="grid size-11 place-items-center rounded-xl bg-cyan-300/10 text-lg font-bold text-cyan-300">▦</div><span className="rounded-full border border-slate-700 px-2.5 py-1 text-[11px] text-slate-400">{getTeamName(project)}</span></div><h3 className="mt-5 text-lg font-semibold text-white">{project.name}</h3><p className="mt-2 min-h-10 line-clamp-2 text-sm leading-5 text-slate-400">{project.description || 'No description provided.'}</p><div className="mt-5 border-t border-slate-800 pt-4"><Link to={`/projects/${project.id}`} className="text-sm font-semibold text-cyan-300 hover:text-cyan-200">Open project <span className="transition group-hover:translate-x-1">→</span></Link></div></article>)}</div>}</section>
    </div>
  </>;
}
