import { useCallback, useEffect, useState, type FormEvent } from 'react';
import { Link, useParams } from 'react-router-dom';
import PageHeader from '../components/PageHeader';
import Notice from '../components/Notice';
import StatusBadge from '../components/StatusBadge';
import EmptyState from '../components/EmptyState';
import api from '../services/api';
import { ENDPOINTS } from '../services/endpoints';
import { formatDate, getErrorMessage, listFromResponse } from '../lib/apiHelpers';
import { useAuth } from '../context/AuthContext';
import type { ActivityItem, Project, Task } from '../types';

type TeamRole = 'OWNER' | 'ADMIN' | 'MEMBER';
type ProjectRole = 'MANAGER' | 'MEMBER' | 'VIEWER';
type TeamMember = { id: number; user: number; username: string; team: number; role: TeamRole; joined_at?: string };
type ProjectMember = { id: number; user: number; username: string; project: number; role: ProjectRole; joined_at?: string };
type AITaskSuggestion = { title: string; description: string; priority: 'high' | 'medium' | 'low' };

export default function ProjectDetailPage() {
  const { user } = useAuth();
  const { projectId: rawId } = useParams();
  const projectId = Number(rawId);
  const [project, setProject] = useState<Project | null>(null);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [activity, setActivity] = useState<ActivityItem[]>([]);
  const [members, setMembers] = useState<ProjectMember[]>([]);
  const [teamMembers, setTeamMembers] = useState<TeamMember[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [activityError, setActivityError] = useState('');
  const [memberError, setMemberError] = useState('');
  const [memberSuccess, setMemberSuccess] = useState('');
  const [memberUsername, setMemberUsername] = useState('');
  const [memberRole, setMemberRole] = useState<'MEMBER' | 'VIEWER'>('MEMBER');
  const [memberSaving, setMemberSaving] = useState(false);
  const [aiSuggestions, setAiSuggestions] = useState<AITaskSuggestion[]>([]);
  const [aiLoading, setAiLoading] = useState(false);
  const [aiError, setAiError] = useState('');
  const [aiSuccess, setAiSuccess] = useState('');

  const load = useCallback(async () => {
    if (!Number.isFinite(projectId) || projectId <= 0) { setError('Invalid project ID.'); setLoading(false); return; }
    setLoading(true);
    setError('');
    setActivityError('');
    setMemberError('');
    const [projectResult, taskResult, activityResult] = await Promise.allSettled([
      api.get<Project>(`${ENDPOINTS.projects}${projectId}/`),
      api.get(`${ENDPOINTS.tasks}?project=${projectId}`),
      api.get(ENDPOINTS.projectActivity(projectId)),
    ]);
    if (projectResult.status === 'fulfilled') {
      const loadedProject = projectResult.value.data;
      setProject(loadedProject);
      const teamId = typeof loadedProject.team === 'number' ? loadedProject.team : loadedProject.team.id;
      const [projectMembersResult, teamMembersResult] = await Promise.allSettled([
        api.get(`${ENDPOINTS.projects}${projectId}/members/`),
        api.get(`${ENDPOINTS.teams}${teamId}/members/`),
      ]);
      if (projectMembersResult.status === 'fulfilled') setMembers(listFromResponse<ProjectMember>(projectMembersResult.value.data));
      else { setMembers([]); setMemberError(getErrorMessage(projectMembersResult.reason, 'Could not load project members.')); }
      if (teamMembersResult.status === 'fulfilled') setTeamMembers(listFromResponse<TeamMember>(teamMembersResult.value.data));
      else { setTeamMembers([]); setMemberError((current) => current || getErrorMessage(teamMembersResult.reason, 'Could not load team membership.')); }
    } else {
      setProject(null);
      setMembers([]);
      setTeamMembers([]);
      setError(getErrorMessage(projectResult.reason, 'Could not load this project.'));
    }
    if (taskResult.status === 'fulfilled') setTasks(listFromResponse<Task>(taskResult.value.data));
    else setTasks([]);
    if (activityResult.status === 'fulfilled') setActivity(listFromResponse<ActivityItem>(activityResult.value.data));
    else setActivityError('Project activity could not be loaded. Check the activity URL in services/endpoints.ts.');
    setLoading(false);
  }, [projectId]);

  useEffect(() => { void load(); }, [load]);

  const myProjectRole = members.find((member) => member.user === user?.id)?.role;
  const myTeamRole = teamMembers.find((member) => member.user === user?.id)?.role;
  const canManageMembers = myProjectRole === 'MANAGER' || myTeamRole === 'OWNER' || myTeamRole === 'ADMIN';

  async function handleGenerateAITasks() {
    if (!project) return;
    setAiLoading(true);
    setAiError('');
    setAiSuccess('');
    setAiSuggestions([]);
    try {
      const response = await api.post<{
        project_id: number;
        project_name: string;
        suggestions: AITaskSuggestion[];
      }>(ENDPOINTS.aiTaskPlanner(projectId), {
        description: project.description?.trim() || '',
      });
      setAiSuggestions(response.data.suggestions);
      setAiSuccess(`Generated ${response.data.suggestions.length} suggestions. Review them below before creating tasks.`);
    } catch (caught) {
      setAiError(getErrorMessage(caught, 'Could not generate task suggestions. Please try again.'));
    } finally {
      setAiLoading(false);
    }
  }

  async function handleAddMember(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setMemberSaving(true);
    setMemberError('');
    setMemberSuccess('');
    try {
      await api.post(`${ENDPOINTS.projects}${projectId}/members/`, { username: memberUsername.trim(), role: memberRole });
      const addedUsername = memberUsername.trim();
      setMemberUsername('');
      setMemberRole('MEMBER');
      setMemberSuccess(`Added ${addedUsername} to this project.`);
      await load();
    } catch (caught) {
      setMemberError(getErrorMessage(caught, 'Could not add this user. Check the username and your permissions.'));
    } finally {
      setMemberSaving(false);
    }
  }

  async function handleChangeRole(member: ProjectMember, role: 'MEMBER' | 'VIEWER') {
    setMemberError('');
    setMemberSuccess('');
    try {
      await api.patch(`${ENDPOINTS.projects}${projectId}/members/${member.id}/role/`, { role });
      setMemberSuccess(`Updated ${member.username}'s project role.`);
      await load();
    } catch (caught) {
      setMemberError(getErrorMessage(caught, 'Could not change the member role.'));
    }
  }

  async function handleRemoveMember(member: ProjectMember) {
    if (!window.confirm(`Remove ${member.username} from this project?`)) return;
    setMemberError('');
    setMemberSuccess('');
    try {
      await api.delete(`${ENDPOINTS.projects}${projectId}/members/${member.id}/`);
      setMemberSuccess(`Removed ${member.username} from this project.`);
      await load();
    } catch (caught) {
      setMemberError(getErrorMessage(caught, 'Could not remove this member.'));
    }
  }

  return <>
    <div className="mb-5"><Link to="/projects" className="text-sm font-semibold text-cyan-300 hover:text-cyan-200">← All projects</Link></div>
    {error && <Notice message={error} />}
    {loading ? <div className="mt-5 rounded-2xl border border-slate-800 p-8 text-sm text-slate-500">Loading project…</div> : project ? <>
      <PageHeader title={project.name} description={project.description || 'Project workspace'} action={<Link to="/tasks" className="rounded-xl bg-cyan-300 px-4 py-2.5 text-sm font-bold text-slate-950 hover:bg-cyan-200">Go to tasks ↗</Link>} />
      <section className="mb-6 rounded-2xl border border-cyan-400/20 bg-gradient-to-br from-cyan-400/10 via-slate-900/70 to-slate-900/50 p-5 sm:p-6">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div className="max-w-2xl">
            <div className="mb-2 inline-flex items-center gap-2 rounded-full border border-cyan-300/20 bg-cyan-300/10 px-3 py-1 text-xs font-semibold text-cyan-200">
              <span aria-hidden="true">✦</span> AI POWERED
            </div>
            <h2 className="text-lg font-semibold text-white">AI Task Planner</h2>
            <p className="mt-1 text-sm leading-6 text-slate-400">Turn this project's description into five actionable task suggestions with priorities. Review the suggestions before creating tasks.</p>
          </div>
          <button type="button" onClick={() => void handleGenerateAITasks()} disabled={aiLoading} className="shrink-0 rounded-xl bg-cyan-300 px-4 py-3 text-sm font-bold text-slate-950 transition hover:bg-cyan-200 disabled:cursor-not-allowed disabled:opacity-60">
            {aiLoading ? 'Generating suggestions…' : aiSuggestions.length ? 'Generate again' : '✦ Generate tasks with AI'}
          </button>
        </div>
        {!project.description?.trim() && <p className="mt-3 text-xs text-amber-200">This project has no description. Add a project description for more relevant suggestions.</p>}
        {aiError && <div className="mt-4"><Notice message={aiError} /></div>}
        {aiSuccess && <div className="mt-4"><Notice kind="success" message={aiSuccess} /></div>}
        {aiSuggestions.length > 0 && <div className="mt-5 grid gap-3 lg:grid-cols-2">
          {aiSuggestions.map((suggestion, index) => {
            const priorityClass = suggestion.priority === 'high'
              ? 'border-rose-400/20 bg-rose-400/10 text-rose-200'
              : suggestion.priority === 'medium'
                ? 'border-amber-300/20 bg-amber-300/10 text-amber-100'
                : 'border-emerald-300/20 bg-emerald-300/10 text-emerald-200';
            return <article key={`${index}-${suggestion.title}`} className="rounded-xl border border-slate-700/80 bg-slate-950/50 p-4">
              <div className="flex items-start justify-between gap-3">
                <div className="flex min-w-0 gap-3">
                  <span className="grid size-8 shrink-0 place-items-center rounded-lg bg-slate-800 text-xs font-bold text-cyan-200">{String(index + 1).padStart(2, '0')}</span>
                  <h3 className="pt-1 text-sm font-semibold text-slate-100">{suggestion.title}</h3>
                </div>
                <span className={`shrink-0 rounded-full border px-2.5 py-1 text-[11px] font-semibold capitalize ${priorityClass}`}>{suggestion.priority}</span>
              </div>
              <p className="mt-3 pl-11 text-sm leading-6 text-slate-400">{suggestion.description}</p>
            </article>;
          })}
        </div>}
      </section>

      <div className="mb-6 grid gap-4 sm:grid-cols-3"><div className="rounded-2xl border border-slate-800 bg-slate-900/50 p-5"><p className="text-xs text-slate-500">Project ID</p><p className="mt-2 text-2xl font-bold text-white">#{project.id}</p></div><div className="rounded-2xl border border-slate-800 bg-slate-900/50 p-5"><p className="text-xs text-slate-500">Tasks</p><p className="mt-2 text-2xl font-bold text-white">{tasks.length}</p></div><div className="rounded-2xl border border-slate-800 bg-slate-900/50 p-5"><p className="text-xs text-slate-500">Created</p><p className="mt-2 text-2xl font-bold text-white">{formatDate(project.created_at)}</p></div></div>

      <section className="mb-6 rounded-2xl border border-slate-800 bg-slate-900/50 p-5 sm:p-6">
        <div className="mb-4 flex flex-wrap items-start justify-between gap-3"><div><h2 className="font-semibold text-white">Project members</h2><p className="mt-1 text-sm text-slate-400">Manage who can access this project.</p></div><span className="rounded-full bg-slate-800 px-3 py-1 text-xs text-slate-300">{members.length} members</span></div>
        {memberError && <div className="mb-3"><Notice message={memberError} /></div>}
        {memberSuccess && <div className="mb-3"><Notice kind="success" message={memberSuccess} /></div>}
        {members.length === 0 ? <p className="mb-4 text-sm text-slate-500">No project membership details were returned.</p> : <div className="mb-5 grid gap-2 md:grid-cols-2">{members.map((member) => <div key={member.id} className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-slate-800 bg-slate-950/50 px-3 py-3"><div className="min-w-0"><p className="truncate text-sm font-medium text-slate-200">{member.username}{member.user === user?.id ? ' (you)' : ''}</p><p className="mt-1 text-xs text-slate-500">{member.role}{member.joined_at ? ` · Joined ${formatDate(member.joined_at)}` : ''}</p></div>{canManageMembers && member.role !== 'MANAGER' && <div className="flex items-center gap-2"><label className="sr-only" htmlFor={`project-role-${member.id}`}>Project role for {member.username}</label><select id={`project-role-${member.id}`} value={member.role} onChange={(event) => void handleChangeRole(member, event.target.value as 'MEMBER' | 'VIEWER')} className="rounded-lg border border-slate-700 bg-slate-900 px-2 py-2 text-xs text-slate-200"><option value="MEMBER">Member</option><option value="VIEWER">Viewer</option></select><button onClick={() => void handleRemoveMember(member)} className="rounded-lg px-2 py-2 text-xs text-rose-300 hover:bg-rose-400/10">Remove</button></div>}</div>)}</div>}
        {canManageMembers ? <form onSubmit={(event) => void handleAddMember(event)} className="grid gap-3 rounded-xl border border-slate-800 bg-slate-950/40 p-4 sm:grid-cols-[1fr_150px_auto]"><label className="block"><span className="mb-1.5 block text-xs text-slate-400">Registered username</span><input required value={memberUsername} onChange={(event) => setMemberUsername(event.target.value)} placeholder="e.g. alex" className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2.5 text-sm text-white outline-none focus:border-cyan-300" /></label><label className="block"><span className="mb-1.5 block text-xs text-slate-400">Project role</span><select value={memberRole} onChange={(event) => setMemberRole(event.target.value as 'MEMBER' | 'VIEWER')} className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2.5 text-sm text-white"><option value="MEMBER">Member</option><option value="VIEWER">Viewer</option></select></label><button disabled={memberSaving || !memberUsername.trim()} className="self-end rounded-lg bg-cyan-300 px-4 py-2.5 text-sm font-bold text-slate-950 disabled:opacity-50">{memberSaving ? 'Adding…' : 'Add member'}</button></form> : <p className="rounded-xl bg-slate-950/50 p-3 text-xs leading-5 text-slate-500">Only the project manager or a team owner/admin can manage project membership. Add an existing account by username; invitations by email are not available yet.</p>}
      </section>

      <div className="grid gap-6 xl:grid-cols-2"><section className="rounded-2xl border border-slate-800 bg-slate-900/50 p-5 sm:p-6"><div className="mb-4 flex items-center justify-between"><div><h2 className="font-semibold text-white">Project tasks</h2><p className="mt-1 text-xs text-slate-500">Work associated with this project</p></div><Link to="/tasks" className="text-xs font-semibold text-cyan-300">Manage tasks →</Link></div>{tasks.length === 0 ? <EmptyState title="No tasks in this project" description="Create a task and choose this project from the task form." /> : <div className="divide-y divide-slate-800">{tasks.slice(0, 8).map((task) => <div key={task.id} className="flex items-center justify-between gap-3 py-3"><div className="min-w-0"><p className="truncate text-sm font-medium text-slate-200">{task.title}</p><p className="mt-1 text-xs text-slate-500">Due {formatDate(task.due_date)}</p></div><StatusBadge value={task.status} /></div>)}</div>}</section>
      <section className="rounded-2xl border border-slate-800 bg-slate-900/50 p-5 sm:p-6"><div className="mb-4"><h2 className="font-semibold text-white">Activity</h2><p className="mt-1 text-xs text-slate-500">Recent project events</p></div>{activityError && <div className="mb-3"><Notice kind="info" message={activityError} /></div>}{activity.length === 0 ? <EmptyState title="No activity to show" description="Project and task events will appear here when the API returns activity records." /> : <div className="space-y-4">{activity.slice(0, 10).map((item) => <div key={item.id} className="flex gap-3"><div className="mt-1 grid size-8 shrink-0 place-items-center rounded-full bg-cyan-300/10 text-cyan-300">↗</div><div className="min-w-0"><p className="text-sm text-slate-200">{item.actor_username || 'A team member'} <span className="text-slate-400">{item.action.replaceAll('_', ' ').toLowerCase()}</span></p><p className="mt-1 text-xs text-slate-500">{formatDate(item.created_at)}</p></div></div>)}</div>}</section></div>
    </> : null}
  </>;
}
