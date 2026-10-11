import { useCallback, useEffect, useState, type FormEvent } from 'react';
import PageHeader from '../components/PageHeader';
import Notice from '../components/Notice';
import EmptyState from '../components/EmptyState';
import api from '../services/api';
import { ENDPOINTS } from '../services/endpoints';
import { getErrorMessage, formatDate, listFromResponse } from '../lib/apiHelpers';
import { useAuth } from '../context/AuthContext';
import type { Team } from '../types';

type TeamRole = 'OWNER' | 'ADMIN' | 'MEMBER';
type TeamMember = {
  id: number;
  user: number;
  username: string;
  team: number;
  role: TeamRole;
  joined_at?: string;
};

export default function TeamsPage() {
  const { user } = useAuth();
  const [teams, setTeams] = useState<Team[]>([]);
  const [name, setName] = useState('');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [expandedTeamId, setExpandedTeamId] = useState<number | null>(null);
  const [membersByTeam, setMembersByTeam] = useState<Record<number, TeamMember[]>>({});
  const [membersLoading, setMembersLoading] = useState(false);
  const [memberUsername, setMemberUsername] = useState('');
  const [memberRole, setMemberRole] = useState<'ADMIN' | 'MEMBER'>('MEMBER');
  const [memberSaving, setMemberSaving] = useState(false);

  const loadTeams = useCallback(async () => {
    setLoading(true);
    try {
      const response = await api.get(ENDPOINTS.teams);
      setTeams(listFromResponse<Team>(response.data));
      setError('');
    } catch (caught) {
      setError(getErrorMessage(caught, 'Could not load teams.'));
    } finally {
      setLoading(false);
    }
  }, []);

  const loadMembers = useCallback(async (teamId: number) => {
    setMembersLoading(true);
    try {
      const response = await api.get(`${ENDPOINTS.teams}${teamId}/members/`);
      setMembersByTeam((current) => ({ ...current, [teamId]: listFromResponse<TeamMember>(response.data) }));
      setError('');
    } catch (caught) {
      setError(getErrorMessage(caught, 'Could not load team members.'));
    } finally {
      setMembersLoading(false);
    }
  }, []);

  useEffect(() => { void loadTeams(); }, [loadTeams]);

  async function handleCreate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSaving(true);
    setError('');
    setSuccess('');
    try {
      await api.post(ENDPOINTS.teams, { name: name.trim() });
      setName('');
      setSuccess('Team created. You are its owner and can add registered users.');
      await loadTeams();
    } catch (caught) {
      setError(getErrorMessage(caught, 'Could not create the team.'));
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete(team: Team) {
    if (!window.confirm(`Delete the team “${team.name}”? Related project data may also be affected.`)) return;
    setError('');
    setSuccess('');
    try {
      await api.delete(`${ENDPOINTS.teams}${team.id}/`);
      setTeams((current) => current.filter((item) => item.id !== team.id));
      setSuccess('Team deleted.');
      if (expandedTeamId === team.id) setExpandedTeamId(null);
    } catch (caught) {
      setError(getErrorMessage(caught, 'Could not delete the team. Only its owner can do this.'));
    }
  }

  async function toggleMembers(team: Team) {
    setError('');
    setSuccess('');
    if (expandedTeamId === team.id) {
      setExpandedTeamId(null);
      return;
    }
    setExpandedTeamId(team.id);
    setMemberUsername('');
    setMemberRole('MEMBER');
    await loadMembers(team.id);
  }

  async function handleAddMember(event: FormEvent<HTMLFormElement>, team: Team) {
    event.preventDefault();
    setMemberSaving(true);
    setError('');
    setSuccess('');
    try {
      await api.post(`${ENDPOINTS.teams}${team.id}/members/`, {
        username: memberUsername.trim(),
        role: memberRole,
      });
      setMemberUsername('');
      setMemberRole('MEMBER');
      setSuccess(`Added ${memberUsername.trim()} to ${team.name}.`);
      await loadMembers(team.id);
    } catch (caught) {
      setError(getErrorMessage(caught, 'Could not add this user. Check the username and your team permissions.'));
    } finally {
      setMemberSaving(false);
    }
  }

  async function handleChangeRole(team: Team, member: TeamMember, role: 'ADMIN' | 'MEMBER') {
    setError('');
    setSuccess('');
    try {
      await api.patch(`${ENDPOINTS.teams}${team.id}/members/${member.id}/role/`, { role });
      setSuccess(`Updated ${member.username}'s team role.`);
      await loadMembers(team.id);
    } catch (caught) {
      setError(getErrorMessage(caught, 'Could not change this member role. Only the team owner can do this.'));
    }
  }

  async function handleRemoveMember(team: Team, member: TeamMember) {
    if (!window.confirm(`Remove ${member.username} from ${team.name}?`)) return;
    setError('');
    setSuccess('');
    try {
      await api.delete(`${ENDPOINTS.teams}${team.id}/members/${member.id}/`);
      setSuccess(`Removed ${member.username} from ${team.name}.`);
      await loadMembers(team.id);
    } catch (caught) {
      setError(getErrorMessage(caught, 'Could not remove this member. Only the team owner can do this.'));
    }
  }

  return <>
    <PageHeader title="Teams" description="Create workspaces, manage membership, and organize projects together." />
    {(error || success) && <div className="mb-5"><Notice message={error || success} kind={error ? 'error' : 'success'} /></div>}
    <div className="grid gap-6 xl:grid-cols-[0.75fr_1.25fr]">
      <section className="h-fit rounded-2xl border border-slate-800 bg-slate-900/60 p-5 sm:p-6">
        <h2 className="font-semibold text-white">Create a team</h2>
        <p className="mt-1 text-sm text-slate-400">Start with a clear team name.</p>
        <form onSubmit={handleCreate} className="mt-5 space-y-4">
          <label className="block"><span className="mb-2 block text-sm text-slate-300">Team name</span><input required maxLength={100} value={name} onChange={(event) => setName(event.target.value)} placeholder="e.g. Backend Team" className="w-full rounded-xl border border-slate-700 bg-slate-950 px-4 py-3 text-sm text-white outline-none focus:border-cyan-300" /></label>
          <button disabled={saving || !name.trim()} className="w-full rounded-xl bg-cyan-300 px-4 py-3 text-sm font-bold text-slate-950 hover:bg-cyan-200 disabled:opacity-50">{saving ? 'Creating…' : 'Create team'}</button>
        </form>
        <p className="mt-4 text-xs leading-5 text-slate-500">Members must have an existing TeamFlow account. Add them by username; email invitations are not implemented yet.</p>
      </section>

      <section>
        <div className="mb-3 flex items-center justify-between"><h2 className="font-semibold text-white">Your teams</h2><span className="rounded-full bg-slate-800 px-3 py-1 text-xs text-slate-300">{teams.length}</span></div>
        {loading ? <div className="rounded-2xl border border-slate-800 p-8 text-sm text-slate-500">Loading teams…</div>
          : teams.length === 0 ? <EmptyState title="No teams found" description="Create a team using the form to get started." />
            : <div className="space-y-3">{teams.map((team) => {
              const expanded = expandedTeamId === team.id;
              const members = membersByTeam[team.id] || [];
              const myRole = members.find((member) => member.user === user?.id)?.role;
              const canAdd = myRole === 'OWNER' || myRole === 'ADMIN';
              const isOwner = myRole === 'OWNER';
              return <article key={team.id} className="rounded-2xl border border-slate-800 bg-slate-900/50 p-5 transition hover:border-slate-700">
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div className="flex min-w-0 gap-3"><div className="grid size-10 shrink-0 place-items-center rounded-xl bg-violet-400/10 font-bold text-violet-300">{team.name.slice(0, 1).toUpperCase()}</div><div className="min-w-0"><h3 className="font-semibold text-white">{team.name}</h3><p className="mt-1 text-xs text-slate-500">Team #{team.id}{team.created_at ? ` · Created ${formatDate(team.created_at)}` : ''}</p></div></div>
                  <div className="flex flex-wrap gap-2"><button onClick={() => void toggleMembers(team)} className="rounded-lg border border-cyan-300/30 px-3 py-2 text-xs font-semibold text-cyan-200 hover:bg-cyan-300/10">{expanded ? 'Hide members' : 'Manage members'}</button><button onClick={() => void handleDelete(team)} aria-label={`Delete ${team.name}`} className="rounded-lg px-2 py-2 text-xs text-slate-500 hover:bg-rose-400/10 hover:text-rose-300">Delete team</button></div>
                </div>
                {expanded && <div className="mt-5 border-t border-slate-800 pt-5">
                  <div className="mb-4 flex items-center justify-between gap-3"><div><h4 className="font-semibold text-white">Team members</h4><p className="mt-1 text-xs text-slate-500">Your role: {myRole || 'unknown'}</p></div><span className="rounded-full bg-slate-800 px-3 py-1 text-xs text-slate-300">{members.length}</span></div>
                  {membersLoading ? <p className="text-sm text-slate-500">Loading members…</p> : members.length === 0 ? <p className="text-sm text-slate-500">No membership data is available.</p> : <div className="mb-5 space-y-2">{members.map((member) => <div key={member.id} className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-slate-800 bg-slate-950/60 px-3 py-3"><div className="min-w-0"><p className="truncate text-sm font-medium text-slate-200">{member.username}{member.user === user?.id ? ' (you)' : ''}</p><p className="mt-1 text-xs text-slate-500">{member.role}{member.joined_at ? ` · Joined ${formatDate(member.joined_at)}` : ''}</p></div>{isOwner && member.role !== 'OWNER' && <div className="flex items-center gap-2"><label className="sr-only" htmlFor={`team-role-${team.id}-${member.id}`}>Role for {member.username}</label><select id={`team-role-${team.id}-${member.id}`} value={member.role} onChange={(event) => void handleChangeRole(team, member, event.target.value as 'ADMIN' | 'MEMBER')} className="rounded-lg border border-slate-700 bg-slate-900 px-2 py-2 text-xs text-slate-200"><option value="MEMBER">Member</option><option value="ADMIN">Admin</option></select><button onClick={() => void handleRemoveMember(team, member)} className="rounded-lg px-2 py-2 text-xs text-rose-300 hover:bg-rose-400/10">Remove</button></div>}</div>)}</div>}
                  {canAdd ? <form onSubmit={(event) => void handleAddMember(event, team)} className="grid gap-3 rounded-xl border border-slate-800 bg-slate-950/40 p-4 sm:grid-cols-[1fr_140px_auto]"><label className="block"><span className="mb-1.5 block text-xs text-slate-400">Registered username</span><input required value={memberUsername} onChange={(event) => setMemberUsername(event.target.value)} placeholder="e.g. alex" className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2.5 text-sm text-white outline-none focus:border-cyan-300" /></label><label className="block"><span className="mb-1.5 block text-xs text-slate-400">Team role</span><select value={memberRole} onChange={(event) => setMemberRole(event.target.value as 'ADMIN' | 'MEMBER')} className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2.5 text-sm text-white">{isOwner && <option value="ADMIN">Admin</option>}<option value="MEMBER">Member</option></select></label><button disabled={memberSaving || !memberUsername.trim()} className="self-end rounded-lg bg-cyan-300 px-4 py-2.5 text-sm font-bold text-slate-950 disabled:opacity-50">{memberSaving ? 'Adding…' : 'Add member'}</button></form> : <p className="rounded-xl bg-slate-950/50 p-3 text-xs leading-5 text-slate-500">Only team owners and admins can add members. The owner can change roles and remove members.</p>}
                </div>}
              </article>;
            })}</div>}
      </section>
    </div>
  </>;
}
