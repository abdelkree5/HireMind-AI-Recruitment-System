import { NavLink } from "react-router-dom";

export default function AppSidebar({
  navItems,
  portalTitle,
  portalSubtitle,
  brandVariant,
}) {
  const brandTone =
    brandVariant === "company"
      ? "from-brand-500 to-brand-700"
      : "from-amber-400 to-orange-500";

  return (
    <aside className="glass hidden border-r border-slate-200/80 lg:block">
      <div className="sticky top-0 h-screen overflow-y-auto px-5 py-6">
        <div className="rounded-2xl border border-white bg-white/80 p-4 shadow-soft">
          <div className="flex items-center gap-3">
            <span
              className={`h-10 w-10 rounded-xl bg-gradient-to-br ${brandTone} float-pulse shadow-panel`}
            />
            <div>
              <p className="text-sm font-semibold tracking-wide text-slate-900">
                {portalTitle}
              </p>
              <p className="text-xs text-slate-500">{portalSubtitle}</p>
            </div>
          </div>
        </div>

        <nav aria-label="Main navigation" className="mt-5 space-y-2">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                [
                  "group flex items-center justify-between rounded-xl px-3 py-2.5 text-sm font-semibold transition-all",
                  isActive
                    ? "bg-gradient-to-r from-brand-500 to-brand-600 text-white shadow-soft"
                    : "text-slate-600 hover:bg-brand-50 hover:text-brand-700",
                ].join(" ")
              }
            >
              <span>{item.label}</span>
              <span className="h-1.5 w-1.5 rounded-full bg-current opacity-60" />
            </NavLink>
          ))}
        </nav>
      </div>
    </aside>
  );
}
