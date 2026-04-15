import { useState } from "react";
import { Badge, Panel } from "../components/SaaSPrimitives";

function toList(value) {
  return value
    .split(/,|\n/)
    .map((item) => item.trim())
    .filter(Boolean);
}

const INITIAL = {
  title: "",
  description: "",
  skills: "",
};

export default function CompanyAddJobPage({ onCreateJob }) {
  const [form, setForm] = useState(INITIAL);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(event) {
    event.preventDefault();
    setBusy(true);
    setError("");

    try {
      await onCreateJob({
        title: form.title,
        description: form.description,
        required_skills: toList(form.skills),
      });
      setForm(INITIAL);
    } catch (submitError) {
      setError(submitError.message || "Unable to create job right now.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-4">
      <Panel
        title="Create New Job"
        subtitle="Publish job requirements with a clean, fast workflow."
      >
        <form onSubmit={handleSubmit} className="space-y-3">
          <label className="block">
            <span className="mb-1.5 block text-sm font-semibold text-slate-700">
              Title
            </span>
            <input
              value={form.title}
              onChange={(event) =>
                setForm((prev) => ({ ...prev, title: event.target.value }))
              }
              required
              className="w-full rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-sm outline-none focus:border-brand-400 focus:ring-2 focus:ring-brand-100"
              placeholder="Senior Backend Engineer"
            />
          </label>

          <label className="block">
            <span className="mb-1.5 block text-sm font-semibold text-slate-700">
              Description
            </span>
            <textarea
              rows="6"
              value={form.description}
              onChange={(event) =>
                setForm((prev) => ({
                  ...prev,
                  description: event.target.value,
                }))
              }
              required
              className="w-full rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-sm outline-none focus:border-brand-400 focus:ring-2 focus:ring-brand-100"
              placeholder="Describe responsibilities, team context, and outcomes."
            />
          </label>

          <label className="block">
            <span className="mb-1.5 block text-sm font-semibold text-slate-700">
              Required skills (comma separated)
            </span>
            <input
              value={form.skills}
              onChange={(event) =>
                setForm((prev) => ({ ...prev, skills: event.target.value }))
              }
              className="w-full rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-sm outline-none focus:border-brand-400 focus:ring-2 focus:ring-brand-100"
              placeholder="Python, FastAPI, PostgreSQL"
            />
          </label>

          <div className="flex flex-wrap gap-2">
            {toList(form.skills).map((skill) => (
              <Badge key={skill}>{skill}</Badge>
            ))}
          </div>

          {error ? (
            <p className="text-sm font-semibold text-rose-600">{error}</p>
          ) : null}

          <button
            type="submit"
            disabled={busy}
            className="rounded-xl bg-brand-500 px-4 py-2.5 text-sm font-bold text-white transition hover:bg-brand-600 disabled:opacity-60"
          >
            {busy ? "Publishing..." : "Publish Job"}
          </button>
        </form>
      </Panel>
    </div>
  );
}
