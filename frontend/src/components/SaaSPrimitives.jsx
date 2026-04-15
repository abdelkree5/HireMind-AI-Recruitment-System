export function Panel({ title, subtitle, actions, children, className = "" }) {
  return (
    <section
      className={`glass rounded-3xl border border-white/80 p-5 shadow-soft ${className}`}
    >
      {(title || subtitle || actions) && (
        <header className="mb-4 flex flex-wrap items-start justify-between gap-3">
          <div>
            {title ? (
              <h2 className="text-lg font-extrabold text-slate-900">{title}</h2>
            ) : null}
            {subtitle ? (
              <p className="mt-1 text-sm text-slate-600">{subtitle}</p>
            ) : null}
          </div>
          {actions ? <div>{actions}</div> : null}
        </header>
      )}
      {children}
    </section>
  );
}

export function StatCard({ label, value, tone = "brand" }) {
  const toneClass =
    tone === "dark"
      ? "from-slate-900 to-slate-700 text-white"
      : tone === "muted"
        ? "from-slate-100 to-slate-50 text-slate-900"
        : "from-brand-500 to-orange-500 text-white";

  return (
    <article
      className={`rounded-2xl bg-gradient-to-br p-4 shadow-soft ${toneClass}`}
    >
      <p className="text-xs font-semibold uppercase tracking-[0.12em] opacity-90">
        {label}
      </p>
      <p className="mt-2 text-2xl font-black">{value}</p>
    </article>
  );
}

export function Badge({ children }) {
  return (
    <span className="inline-flex rounded-full bg-brand-100 px-2.5 py-1 text-xs font-semibold text-brand-700">
      {children}
    </span>
  );
}

export function EmptyState({ title, hint }) {
  return (
    <div className="rounded-2xl border border-dashed border-slate-300 bg-white/70 p-6 text-center">
      <p className="text-base font-bold text-slate-800">{title}</p>
      <p className="mt-1 text-sm text-slate-500">{hint}</p>
    </div>
  );
}

export function InlineLoader({ text = "Loading..." }) {
  return (
    <div className="inline-flex items-center gap-2 rounded-xl bg-brand-50 px-3 py-2 text-sm font-semibold text-brand-700">
      <span className="h-2 w-2 animate-pulse rounded-full bg-brand-500" />
      {text}
    </div>
  );
}

export function Toast({ type = "success", message, onClose }) {
  if (!message) return null;
  const tone =
    type === "error"
      ? "border-rose-200 bg-rose-50 text-rose-700"
      : "border-emerald-200 bg-emerald-50 text-emerald-700";

  return (
    <div
      className={`fixed bottom-5 right-5 z-50 max-w-sm rounded-2xl border px-4 py-3 shadow-soft ${tone}`}
    >
      <div className="flex items-start justify-between gap-4">
        <p className="text-sm font-semibold">{message}</p>
        <button
          type="button"
          onClick={onClose}
          className="text-xs font-bold uppercase tracking-wide opacity-70 transition hover:opacity-100"
        >
          close
        </button>
      </div>
    </div>
  );
}

export function Modal({ open, title, description, onCancel, onConfirm }) {
  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/35 p-4">
      <div className="w-full max-w-md rounded-3xl border border-white/80 bg-white p-5 shadow-panel">
        <h3 className="text-lg font-extrabold text-slate-900">{title}</h3>
        <p className="mt-2 text-sm text-slate-600">{description}</p>
        <div className="mt-4 flex justify-end gap-2">
          <button
            type="button"
            onClick={onCancel}
            className="rounded-xl border border-slate-200 bg-white px-4 py-2 text-sm font-semibold text-slate-700"
          >
            Cancel
          </button>
          <button
            type="button"
            onClick={onConfirm}
            className="rounded-xl bg-rose-600 px-4 py-2 text-sm font-semibold text-white"
          >
            Confirm
          </button>
        </div>
      </div>
    </div>
  );
}
