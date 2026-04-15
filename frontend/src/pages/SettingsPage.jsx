import { useState } from "react";
import { Panel } from "../components/SaaSPrimitives";

export default function SettingsPage() {
  const [settings, setSettings] = useState({
    notifications: true,
    autoRefresh: true,
    compactMode: false,
  });

  function toggle(key) {
    setSettings((prev) => ({ ...prev, [key]: !prev[key] }));
  }

  return (
    <Panel
      title="Settings"
      subtitle="Control notification and workspace preferences."
    >
      <div className="space-y-3">
        <label className="flex items-center justify-between rounded-2xl border border-slate-200 bg-white px-4 py-3">
          <div>
            <p className="text-sm font-bold text-slate-900">
              Email notifications
            </p>
            <p className="text-xs text-slate-500">
              Get updates for interviews and applications.
            </p>
          </div>
          <input
            type="checkbox"
            checked={settings.notifications}
            onChange={() => toggle("notifications")}
            className="h-4 w-4 accent-brand-500"
          />
        </label>

        <label className="flex items-center justify-between rounded-2xl border border-slate-200 bg-white px-4 py-3">
          <div>
            <p className="text-sm font-bold text-slate-900">
              Auto refresh dashboard
            </p>
            <p className="text-xs text-slate-500">
              Refresh key metrics periodically.
            </p>
          </div>
          <input
            type="checkbox"
            checked={settings.autoRefresh}
            onChange={() => toggle("autoRefresh")}
            className="h-4 w-4 accent-brand-500"
          />
        </label>

        <label className="flex items-center justify-between rounded-2xl border border-slate-200 bg-white px-4 py-3">
          <div>
            <p className="text-sm font-bold text-slate-900">Compact mode</p>
            <p className="text-xs text-slate-500">
              Display denser cards and tables.
            </p>
          </div>
          <input
            type="checkbox"
            checked={settings.compactMode}
            onChange={() => toggle("compactMode")}
            className="h-4 w-4 accent-brand-500"
          />
        </label>
      </div>
    </Panel>
  );
}
