import { useCallback, useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import PageHeader from '../components/PageHeader';
import Notice from '../components/Notice';
import StatusBadge from '../components/StatusBadge';
import EmptyState from '../components/EmptyState';
import api from '../services/api';
import { ENDPOINTS } from '../services/endpoints';
import { formatDate, getErrorMessage, listFromResponse } from '../lib/apiHelpers';
import type { ActivityItem, Project, Task } from '../types';

export default function ProjectDetailPage() {
  const { projectId: rawId } = useParams();
  const projectId = Number(rawId);
  const [project, setProject] = useState<Project | null>(null);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [activity, setActivity] = useState<ActivityItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [activityError, setActivityError] = useState('');

  const load = useCallback(async () => {
    if (!Number.isFinite(projectId)) { setError('Invalid project ID.'); setLoading(false); return; }
    setLoading(true); setError('');
    const [projectResult, taskResult, activityResult] = await Promise.allSettled([
      api.get<Project>(`${ENDPOINTS.projects}${projectId}/`),
      api.get(`${ENDPOINTS.tasks}?project=${projectId}`),
      api.get(ENDPOINTS.projectActivity(projectId)),
    ]);
    if (projectResult.status === 'fulfilled') setProject(projectResult.value.data);
    else setError(getErrorMessage(projectResult.reason, 'Could not load this project.'));
    if (taskResult.status === 'fulfilled') setTasks(listFromResponse<Task>(taskResult.value.data));
    if (activityResult.status === 'fulfilled') setActivity(listFromResponse<ActivityItem>(activityResult.value.data));
    else setActivityError('Project activity could not be loaded. Check the activity URL in services/endpoints.ts.');
    setLoading(false);
  }, [projectId]);

  useEffect(() => { void load(); }, [load]);

  return <>
    <div className="mb-5"><Link to="/projects" className="text-sm font-semibold text-cyan-300 hover:text-cyan-200">← All projects</Link></div>
    {error && <Notice message={error} />}
    {loading ? <div className="mt-5 rounded-2xl border border-slate-800 p-8 text-sm text-slate-500">Loading project…</div> : project ? <>
      <PageHeader title={project.name} description={project.description || 'Project workspace'} action={<Link to="/tasks" className="rounded-xl bg-cyan-300 px-4 py-2.5 text-sm font-bold text-slate-950 hover:bg-cyan-200">Go to tasks ↗</Link>} />
      <div className="mb-6 grid gap-4 sm:grid-cols-3"><div className="rounded-2xl border border-slate-800 bg-slate-900/50 p-5"><p className="text-xs text-slate-500">Project ID</p><p className="mt-2 text-2xl font-bold text-white">#{project.id}</p></div><div className="rounded-2xl border border-slate-800 bg-slate-900/50 p-5"><p className="text-xs text-slate-500">Tasks</p><p className="mt-2 text-2xl font-bold text-white">{tasks.length}</p></div><div className="rounded-2xl border border-slate-800 bg-slate-900/50 p-5"><p className="text-xs text-slate-500">Created</p><p className="mt-2 text-2xl font-bold text-white">{formatDate(project.created_at)}</p></div></div>
      <div className="grid gap-6 xl:grid-cols-2"><section className="rounded-2xl border border-slate-800 bg-slate-900/50 p-5 sm:p-6"><div className="mb-4 flex items-center justify-between"><div><h2 className="font-semibold text-white">Project tasks</h2><p className="mt-1 text-xs text-slate-500">Work associated with this project</p></div><Link to="/tasks" className="text-xs font-semibold text-cyan-300">Manage tasks →</Link></div>{tasks.length === 0 ? <EmptyState title="No tasks in this project" description="Create a task and choose this project from the task form." /> : <div className="divide-y divide-slate-800">{tasks.slice(0, 8).map((task) => <div key={task.id} className="flex items-center justify-between gap-3 py-3"><div className="min-w-0"><p className="truncate text-sm font-medium text-slate-200">{task.title}</p><p className="mt-1 text-xs text-slate-500">Due {formatDate(task.due_date)}</p></div><StatusBadge value={task.status} /></div>)}</div>}</section>
      <section className="rounded-2xl border border-slate-800 bg-slate-900/50 p-5 sm:p-6"><div className="mb-4"><h2 className="font-semibold text-white">Activity</h2><p className="mt-1 text-xs text-slate-500">Recent project events</p></div>{activityError && <div className="mb-3"><Notice kind="info" message={activityError} /></div>}{activity.length === 0 ? <EmptyState title="No activity to show" description="Project and task events will appear here when the API returns activity records." /> : <div className="space-y-4">{activity.slice(0, 10).map((item) => <div key={item.id} className="flex gap-3"><div className="mt-1 grid size-8 shrink-0 place-items-center rounded-full bg-cyan-300/10 text-cyan-300">↗</div><div className="min-w-0"><p className="text-sm text-slate-200">{item.actor_username || 'A team member'} <span className="text-slate-400">{item.action.replaceAll('_', ' ').toLowerCase()}</span></p><p className="mt-1 text-xs text-slate-500">{formatDate(item.created_at)}</p></div></div>)}</div>}</section></div>
    </> : null}
  </>;
}
