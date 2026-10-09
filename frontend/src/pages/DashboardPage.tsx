import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import PageHeader from '../components/PageHeader';
import Notice from '../components/Notice';
import StatusBadge from '../components/StatusBadge';
import EmptyState from '../components/EmptyState';
import api from '../services/api';
import { ENDPOINTS } from '../services/endpoints';
import { formatDate, listFromResponse } from '../lib/apiHelpers';
import type { NotificationItem, Project, Task, Team } from '../types';

export default function DashboardPage() {
  const [teams, setTeams] = useState<Team[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [notifications, setNotifications] = useState<NotificationItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    let active = true;
    async function load() {
      setLoading(true);
      const results = await Promise.allSettled([
        api.get(ENDPOINTS.teams), api.get(ENDPOINTS.projects), api.get(ENDPOINTS.tasks), api.get(ENDPOINTS.notifications),
      ]);
      if (!active) return;
      const [teamsResult, projectsResult, tasksResult, notificationsResult] = results;
      if (teamsResult.status === 'fulfilled') setTeams(listFromResponse<Team>(teamsResult.value.data));
      if (projectsResult.status === 'fulfilled') setProjects(listFromResponse<Project>(projectsResult.value.data));
      if (tasksResult.status === 'fulfilled') setTasks(listFromResponse<Task>(tasksResult.value.data));
      if (notificationsResult.status === 'fulfilled') setNotifications(listFromResponse<NotificationItem>(notificationsResult.value.data));
      if (results.every((result) => result.status === 'rejected')) setError('Could not load dashboard data. Check the API routes and Django server.');
      setLoading(false);
    }
    void load();
    return () => { active = false; };
  }, []);

  const openTasks = tasks.filter((task) => !['done', 'completed', 'complete'].includes((task.status || '').toLowerCase())).length;
  const unread = notifications.filter((item) => !item.read_at).length;
  const stats = [
    { label: 'Teams', value: teams.length, helper: 'Workspaces you belong to', symbol: '◉', tone: 'text-cyan-300 bg-cyan-300/10' },
    { label: 'Projects', value: projects.length, helper: 'Active project spaces', symbol: '▦', tone: 'text-violet-300 bg-violet-300/10' },
    { label: 'Open tasks', value: openTasks, helper: 'Tasks not marked complete', symbol: '✓', tone: 'text-amber-300 bg-amber-300/10' },
    { label: 'Unread alerts', value: unread, helper: 'Notifications to review', symbol: '♧', tone: 'text-emerald-300 bg-emerald-300/10' },
  ];

  return <>
    <PageHeader title="Overview" description="A snapshot of your teams, projects, and the work that needs attention." action={<Link to="/projects" className="rounded-xl bg-cyan-300 px-4 py-2.5 text-sm font-bold text-slate-950 transition hover:bg-cyan-200">Browse projects ↗</Link>} />
    {error && <div className="mb-5"><Notice message={error} /></div>}
    <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">{stats.map((stat) => <div key={stat.label} className="rounded-2xl border border-slate-800 bg-slate-900/70 p-5"><div className="flex items-start justify-between"><span className="text-sm text-slate-400">{stat.label}</span><span className={`grid size-9 place-items-center rounded-xl ${stat.tone}`}>{stat.symbol}</span></div><p className="mt-5 text-3xl font-bold tracking-tight text-white">{loading ? '—' : stat.value}</p><p className="mt-1 text-xs text-slate-500">{stat.helper}</p></div>)}</div>
    <div className="mt-7 grid gap-6 xl:grid-cols-[1.35fr_0.65fr]">
      <section className="rounded-2xl border border-slate-800 bg-slate-900/50 p-5 sm:p-6"><div className="mb-5 flex items-center justify-between"><div><h2 className="font-semibold text-white">Recent tasks</h2><p className="mt-1 text-xs text-slate-500">Across projects you can access</p></div><Link to="/tasks" className="text-xs font-semibold text-cyan-300 hover:text-cyan-200">All tasks →</Link></div>
        {loading ? <p className="py-8 text-sm text-slate-500">Loading tasks…</p> : tasks.length === 0 ? <EmptyState title="No tasks yet" description="Create a task in a project to start tracking work here." /> : <div className="divide-y divide-slate-800">{tasks.slice(0, 6).map((task) => <div key={task.id} className="flex flex-col gap-3 py-4 sm:flex-row sm:items-center sm:justify-between"><div className="min-w-0"><p className="truncate text-sm font-semibold text-slate-200">{task.title}</p><p className="mt-1 line-clamp-1 text-xs text-slate-500">{task.description || 'No description'} · Due {formatDate(task.due_date)}</p></div><div className="flex shrink-0 gap-2"><StatusBadge value={task.priority} /><StatusBadge value={task.status} /></div></div>)}</div>}
      </section>
      <section className="rounded-2xl border border-slate-800 bg-slate-900/50 p-5 sm:p-6"><div className="mb-5 flex items-center justify-between"><div><h2 className="font-semibold text-white">Your projects</h2><p className="mt-1 text-xs text-slate-500">Recently available</p></div><Link to="/projects" className="text-xs font-semibold text-cyan-300 hover:text-cyan-200">View all →</Link></div>
        {loading ? <p className="py-8 text-sm text-slate-500">Loading projects…</p> : projects.length === 0 ? <EmptyState title="No projects yet" description="Create your first project to organize tasks." /> : <div className="space-y-3">{projects.slice(0, 5).map((project) => <Link key={project.id} to={`/projects/${project.id}`} className="block rounded-xl border border-slate-800 bg-slate-950/60 p-4 transition hover:border-cyan-400/30"><p className="truncate text-sm font-semibold text-white">{project.name}</p><p className="mt-1 line-clamp-2 text-xs leading-5 text-slate-500">{project.description || 'No description provided.'}</p><p className="mt-3 text-[11px] text-cyan-300">Open project ↗</p></Link>)}</div>}
      </section>
    </div>
  </>;
}
