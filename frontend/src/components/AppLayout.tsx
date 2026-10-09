import { NavLink, Outlet, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const links = [
  { to: '/dashboard', label: 'Overview', icon: '◫' },
  { to: '/teams', label: 'Teams', icon: '◉' },
  { to: '/projects', label: 'Projects', icon: '▦' },
  { to: '/tasks', label: 'Tasks', icon: '✓' },
  { to: '/notifications', label: 'Notifications', icon: '♧' },
];

export default function AppLayout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const current = links.find((link) => location.pathname === link.to || (link.to === '/projects' && location.pathname.startsWith('/projects/')));

  function handleLogout() {
    logout();
    navigate('/login', { replace: true });
  }

  const navigation = (mobile = false) => links.map((link) => (
    <NavLink
      key={link.to}
      to={link.to}
      className={({ isActive }) => `flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition ${isActive || (link.to === '/projects' && location.pathname.startsWith('/projects/')) ? 'bg-cyan-400/10 text-cyan-200 ring-1 ring-cyan-300/15' : 'text-slate-400 hover:bg-slate-800 hover:text-white'} ${mobile ? 'justify-center px-2 text-xs' : ''}`}
    >
      <span className="grid size-6 shrink-0 place-items-center text-base">{link.icon}</span>
      <span>{link.label}</span>
    </NavLink>
  ));

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 lg:flex">
      <aside className="hidden w-64 shrink-0 border-r border-slate-800/80 bg-slate-950 px-5 py-6 lg:flex lg:flex-col">
        <div className="mb-10 flex items-center gap-3 px-2">
          <div className="grid size-10 place-items-center rounded-xl bg-cyan-300 font-black text-slate-950">TF</div>
          <div><p className="font-bold tracking-wide text-white">TeamFlow</p><p className="text-xs text-slate-500">Work, in sync.</p></div>
        </div>
        <p className="mb-3 px-3 text-[10px] font-bold uppercase tracking-[0.2em] text-slate-600">Workspace</p>
        <nav className="space-y-1">{navigation()}</nav>
        <div className="mt-auto rounded-2xl border border-slate-800 bg-slate-900/70 p-4">
          <p className="text-xs font-semibold text-slate-300">Backend connected</p>
          <p className="mt-1 text-xs leading-5 text-slate-500">Django REST API · JWT auth</p>
          <div className="mt-3 flex items-center gap-2 text-xs text-emerald-300"><span className="size-1.5 rounded-full bg-emerald-400" /> Local development</div>
        </div>
      </aside>

      <div className="min-w-0 flex-1">
        <header className="sticky top-0 z-20 flex items-center justify-between border-b border-slate-800/80 bg-slate-950/90 px-4 py-4 backdrop-blur-xl sm:px-7">
          <div className="flex items-center gap-3">
            <div className="grid size-9 place-items-center rounded-xl bg-cyan-300 font-black text-slate-950 lg:hidden">TF</div>
            <div><p className="text-sm font-semibold text-white">{current?.label || 'Project workspace'}</p><p className="text-xs text-slate-500">Manage work with clarity</p></div>
          </div>
          <div className="flex items-center gap-3">
            <div className="hidden text-right sm:block"><p className="text-sm font-semibold text-slate-200">{user?.username || 'User'}</p><p className="text-xs text-slate-500">{user?.email || 'TeamFlow member'}</p></div>
            <div className="grid size-9 place-items-center rounded-full bg-gradient-to-br from-cyan-300 to-blue-500 text-sm font-bold text-slate-950">{(user?.username || 'U').slice(0, 1).toUpperCase()}</div>
            <button onClick={handleLogout} className="rounded-lg border border-slate-700 px-3 py-2 text-xs font-semibold text-slate-300 transition hover:border-rose-400/40 hover:text-rose-200">Log out</button>
          </div>
        </header>
        <nav className="grid grid-cols-5 gap-1 border-b border-slate-800/80 px-2 py-2 lg:hidden">{navigation(true)}</nav>
        <main className="mx-auto w-full max-w-7xl px-4 py-7 sm:px-7 sm:py-9"><Outlet /></main>
        <footer className="px-7 pb-6 text-center text-[11px] text-slate-600">TeamFlow · React + TypeScript · Django REST Framework</footer>
      </div>
    </div>
  );
}
