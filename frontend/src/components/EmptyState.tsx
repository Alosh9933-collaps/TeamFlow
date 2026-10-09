export default function EmptyState({ title, description }: { title: string; description: string }) {
  return (
    <div className="rounded-2xl border border-dashed border-slate-700 bg-slate-900/40 px-6 py-12 text-center">
      <div className="mx-auto mb-4 grid size-12 place-items-center rounded-2xl bg-cyan-400/10 text-xl text-cyan-300">✦</div>
      <h3 className="font-semibold text-white">{title}</h3>
      <p className="mx-auto mt-2 max-w-md text-sm leading-6 text-slate-400">{description}</p>
    </div>
  );
}
