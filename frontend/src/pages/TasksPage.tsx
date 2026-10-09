import { useCallback, useEffect, useState, type FormEvent } from 'react';
import PageHeader from '../components/PageHeader';
import Notice from '../components/Notice';
import EmptyState from '../components/EmptyState';
import StatusBadge from '../components/StatusBadge';
import api from '../services/api';
import { ENDPOINTS } from '../services/endpoints';
import { formatDate, getErrorMessage, listFromResponse, projectIdOf } from '../lib/apiHelpers';
import type { Project, Task } from '../types';

export default function TasksPage() {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [projectId, setProjectId] = useState('');
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [priority, setPriority] = useState('MEDIUM');
  const [dueDate, setDueDate] = useState('');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [filter, setFilter] = useState('ALL');

  const load = useCallback(async () => {
    setLoading(true);
    const [taskResult, projectResult] = await Promise.allSettled([api.get(ENDPOINTS.tasks), api.get(ENDPOINTS.projects)]);
    if (taskResult.status === 'fulfilled') setTasks(listFromResponse<Task>(taskResult.value.data));
    else setError(getErrorMessage(taskResult.reason, 'Could not load tasks.'));
    if (projectResult.status === 'fulfilled') {
      const loaded = listFromResponse<Project>(projectResult.value.data); setProjects(loaded);
      if (!projectId && loaded.length) setProjectId(String(loaded[0].id));
    }
    setLoading(false);
  }, [projectId]);

  useEffect(() => { void load(); }, [load]);

  async function handleCreate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setSaving(true); setError(''); setSuccess('');
    try {
      await api.post(ENDPOINTS.tasks, { project: Number(projectId), title: title.trim(), description: description.trim(), priority, due_date: dueDate || null, tags: [] });
      setTitle(''); setDescription(''); setDueDate(''); setSuccess('Task created.'); await load();
    } catch (caught) { setError(getErrorMessage(caught, 'Could not create task. Check the project membership and task fields.')); }
    finally { setSaving(false); }
  }

  async function runTaskAction(task: Task, action: 'claim' | 'unclaim' | 'complete') {
    setError(''); setSuccess('');
    try {
      await api.post(`${ENDPOINTS.tasks}${task.id}/${action}/`);
      setSuccess(`Task ${action === 'claim' ? 'claimed' : action === 'unclaim' ? 'unclaimed' : 'completed'}.`);
      await load();
    } catch (caught) { setError(getErrorMessage(caught, `Could not ${action} this task.`)); }
  }

  const shownTasks = filter === 'ALL' ? tasks : tasks.filter((task) => (task.status || '').toUpperCase() === filter);
  const getProjectName = (task: Task) => typeof task.project === 'object' ? task.project.name : projects.find((project) => project.id === projectIdOf(task.project))?.name || `Project #${projectIdOf(task.project)}`;

  return <>
    <PageHeader title="Tasks" description="Create tasks, check priorities, and claim or complete work." />
    {(error || success) && <div className="mb-5"><Notice message={error || success} kind={error ? 'error' : 'success'} /></div>}
    <div className="grid gap-6 xl:grid-cols-[0.78fr_1.22fr]">
      <section className="h-fit rounded-2xl border border-slate-800 bg-slate-900/60 p-5 sm:p-6"><h2 className="font-semibold text-white">Create a task</h2><p className="mt-1 text-sm text-slate-400">Tasks belong to a project.</p>{projects.length === 0 && !loading && <div className="mt-4"><Notice message="Create a project before adding tasks." kind="info" /></div>}
        <form onSubmit={handleCreate} className="mt-5 space-y-4"><label className="block"><span className="mb-2 block text-sm text-slate-300">Project</span><select required value={projectId} onChange={(e) => setProjectId(e.target.value)} className="w-full rounded-xl border border-slate-700 bg-slate-950 px-4 py-3 text-sm text-white outline-none focus:border-cyan-300"><option value="">Select project</option>{projects.map((project) => <option key={project.id} value={project.id}>{project.name}</option>)}</select></label><label className="block"><span className="mb-2 block text-sm text-slate-300">Title</span><input required value={title} onChange={(e) => setTitle(e.target.value)} placeholder="e.g. Implement login endpoint" className="w-full rounded-xl border border-slate-700 bg-slate-950 px-4 py-3 text-sm text-white outline-none focus:border-cyan-300" /></label><label className="block"><span className="mb-2 block text-sm text-slate-300">Description</span><textarea rows={3} value={description} onChange={(e) => setDescription(e.target.value)} placeholder="Task details" className="w-full resize-y rounded-xl border border-slate-700 bg-slate-950 px-4 py-3 text-sm text-white outline-none focus:border-cyan-300" /></label><div className="grid grid-cols-2 gap-3"><label className="block"><span className="mb-2 block text-sm text-slate-300">Priority</span><select value={priority} onChange={(e) => setPriority(e.target.value)} className="w-full rounded-xl border border-slate-700 bg-slate-950 px-3 py-3 text-sm text-white outline-none focus:border-cyan-300"><option value="LOW">Low</option><option value="MEDIUM">Medium</option><option value="HIGH">High</option><option value="URGENT">Urgent</option></select></label><label className="block"><span className="mb-2 block text-sm text-slate-300">Due date</span><input type="date" value={dueDate} onChange={(e) => setDueDate(e.target.value)} className="w-full rounded-xl border border-slate-700 bg-slate-950 px-3 py-3 text-sm text-white outline-none focus:border-cyan-300" /></label></div><button disabled={saving || !projectId || !title.trim()} className="w-full rounded-xl bg-cyan-300 px-4 py-3 text-sm font-bold text-slate-950 hover:bg-cyan-200 disabled:opacity-50">{saving ? 'Creating…' : 'Create task'}</button></form>
      </section>
      <section><div className="mb-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between"><div><h2 className="font-semibold text-white">Task list</h2><p className="mt-1 text-xs text-slate-500">{shownTasks.length} task{shownTasks.length === 1 ? '' : 's'}</p></div><select value={filter} onChange={(e) => setFilter(e.target.value)} className="rounded-xl border border-slate-700 bg-slate-900 px-3 py-2.5 text-xs text-slate-200 outline-none focus:border-cyan-300"><option value="ALL">All statuses</option><option value="TODO">To do</option><option value="PENDING">Pending</option><option value="IN_PROGRESS">In progress</option><option value="DONE">Done</option></select></div>
        {loading ? <div className="rounded-2xl border border-slate-800 p-8 text-sm text-slate-500">Loading tasks…</div> : shownTasks.length === 0 ? <EmptyState title="No matching tasks" description="Create your first task or choose a different status filter." /> : <div className="space-y-3">{shownTasks.map((task) => <article key={task.id} className="rounded-2xl border border-slate-800 bg-slate-900/55 p-4 sm:p-5"><div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between"><div className="min-w-0"><div className="flex flex-wrap items-center gap-2"><h3 className="font-semibold text-white">{task.title}</h3><StatusBadge value={task.status} /></div><p className="mt-1 text-xs text-cyan-300">{getProjectName(task)}</p><p className="mt-2 whitespace-pre-line text-sm leading-6 text-slate-400">{task.description || 'No description provided.'}</p></div><div className="flex shrink-0 flex-wrap gap-2"><StatusBadge value={task.priority} /><span className="rounded-full border border-slate-700 px-2.5 py-1 text-xs text-slate-400">Due {formatDate(task.due_date)}</span></div></div><div className="mt-4 flex flex-wrap gap-2 border-t border-slate-800 pt-4"><button onClick={() => void runTaskAction(task, 'claim')} className="rounded-lg border border-slate-700 px-3 py-2 text-xs font-semibold text-slate-300 hover:border-cyan-300/40 hover:text-cyan-200">Claim</button><button onClick={() => void runTaskAction(task, 'unclaim')} className="rounded-lg border border-slate-700 px-3 py-2 text-xs font-semibold text-slate-300 hover:border-amber-300/40 hover:text-amber-200">Unclaim</button><button onClick={() => void runTaskAction(task, 'complete')} className="rounded-lg bg-emerald-400/10 px-3 py-2 text-xs font-semibold text-emerald-300 hover:bg-emerald-400/20">Complete</button></div></article>)}</div>}
      </section>
    </div>
  </>;
}
