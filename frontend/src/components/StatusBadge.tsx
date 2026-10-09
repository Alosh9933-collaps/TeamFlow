import { humanize } from '../lib/apiHelpers';

export default function StatusBadge({ value }: { value?: string | null }) {
  const text = humanize(value);
  const normalized = (value || '').toLowerCase();
  const style = normalized.includes('done') || normalized.includes('complete') || normalized.includes('read') || normalized.includes('approved')
    ? 'bg-emerald-400/10 text-emerald-300 ring-emerald-400/20'
    : normalized.includes('progress') || normalized.includes('pending') || normalized.includes('medium')
      ? 'bg-amber-400/10 text-amber-300 ring-amber-400/20'
      : normalized.includes('high') || normalized.includes('urgent') || normalized.includes('reject')
        ? 'bg-rose-400/10 text-rose-300 ring-rose-400/20'
        : 'bg-slate-400/10 text-slate-300 ring-slate-400/20';
  return <span className={`inline-flex rounded-full px-2.5 py-1 text-xs font-medium ring-1 ring-inset ${style}`}>{text}</span>;
}
