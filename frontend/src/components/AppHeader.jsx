import { useLocation } from "react-router-dom";

export default function AppHeader({
  titles,
  portalLabel,
  searchPlaceholder,
  currentUser,
  onLogout,
}) {
  const location = useLocation();
  const title =
    titles[location.pathname] || Object.values(titles)[0] || "Dashboard";

  return (
    <header className="glass rounded-3xl border border-white/80 p-4 shadow-soft md:p-5">
      <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <p className="text-[11px] font-bold uppercase tracking-[0.18em] text-brand-600">
            {portalLabel}
          </p>
          <h1 className="mt-1 text-xl font-extrabold text-slate-900 md:text-2xl">
            {title}
          </h1>
        </div>

        <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
          <input
            placeholder={searchPlaceholder}
            className="w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700 outline-none transition focus:border-brand-400 focus:ring-2 focus:ring-brand-100 sm:w-72"
          />

          <button
            type="button"
            className="rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm font-semibold text-slate-600 transition hover:border-brand-300 hover:text-brand-700"
          >
            Notifications
          </button>

          {currentUser && (
            <div className="flex items-center gap-2">
              <div className="rounded-xl bg-white px-3 py-2 text-xs font-semibold text-slate-600 shadow-sm">
                <div className="text-slate-800">{currentUser.full_name}</div>
                <div className="uppercase tracking-wide text-brand-600">
                  {currentUser.role}
                </div>
              </div>
              <button
                type="button"
                onClick={onLogout}
                className="rounded-xl bg-slate-900 px-3 py-2 text-sm font-semibold text-white transition hover:bg-slate-700"
              >
                Logout
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
