import type { ReactNode } from 'react';

export default function PageHeader({ title, description, action }: { title: string; description?: string; action?: ReactNode }) {
  return (
    <div className="mb-7 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
      <div>
        <p className="mb-2 text-xs font-semibold uppercase tracking-[0.22em] text-cyan-400">TeamFlow workspace</p>
        <h1 className="text-3xl font-bold tracking-tight text-white">{title}</h1>
        {description && <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-400">{description}</p>}
      </div>
      {action}
    </div>
  );
}
