export default function Notice({ message, kind = 'error' }: { message: string; kind?: 'error' | 'success' | 'info' }) {
  const styles = {
    error: 'border-rose-500/30 bg-rose-500/10 text-rose-200',
    success: 'border-emerald-500/30 bg-emerald-500/10 text-emerald-200',
    info: 'border-cyan-500/30 bg-cyan-500/10 text-cyan-100',
  };
  return <div role="status" className={`rounded-xl border px-4 py-3 text-sm ${styles[kind]}`}>{message}</div>;
}
