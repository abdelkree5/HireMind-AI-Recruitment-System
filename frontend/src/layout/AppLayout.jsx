import { NavLink, Outlet } from "react-router-dom";
import AppHeader from "../components/AppHeader";
import AppSidebar from "../components/AppSidebar";

export default function AppLayout({
  navItems,
  titles,
  portalTitle,
  portalSubtitle,
  brandVariant,
  portalLabel,
  searchPlaceholder,
  portalTheme,
  currentUser,
  onLogout,
}) {
  return (
    <main
      className={`min-h-screen lg:grid lg:grid-cols-[280px_1fr] ${portalTheme || ""}`}
      dir="ltr"
    >
      <AppSidebar
        navItems={navItems}
        portalTitle={portalTitle}
        portalSubtitle={portalSubtitle}
        brandVariant={brandVariant}
      />
      <section className="px-4 py-4 sm:px-6 sm:py-6 lg:px-8">
        <div className="mb-3 flex gap-2 overflow-auto lg:hidden">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                [
                  "whitespace-nowrap rounded-xl border px-3 py-2 text-xs font-semibold",
                  isActive
                    ? "border-brand-300 bg-brand-50 text-brand-700"
                    : "border-slate-200 bg-white text-slate-600",
                ].join(" ")
              }
            >
              {item.label}
            </NavLink>
          ))}
        </div>

        <AppHeader
          titles={titles}
          portalLabel={portalLabel}
          searchPlaceholder={searchPlaceholder}
          currentUser={currentUser}
          onLogout={onLogout}
        />

        <div className="mt-4">
          <Outlet />
        </div>
      </section>
    </main>
  );
}
