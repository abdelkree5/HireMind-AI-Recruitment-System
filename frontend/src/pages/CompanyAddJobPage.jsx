import { useState } from "react";
import { Badge, Panel } from "../components/SaaSPrimitives";

function toList(value) {
  if (!value) return [];
  return value
    .split(/,|\n/)
    .map((item) => item.trim())
    .filter(Boolean);
}

const DOMAINS = [
  "Backend",
  "Frontend",
  "Full Stack",
  "DevOps",
  "Data",
  "AI_ML",
  "Mobile",
  "UI/UX",
  "QA",
  "Security",
  "Product",
  "General",
];

const EXPERIENCE_LEVELS = ["Junior", "Mid", "Senior", "Lead", "Principal"];

const INITIAL = {
  title: "",
  description: "",
  skills: "",
  responsibilities: "",
  preferred_skills: "",
  tools: "",
  experience_level: "Mid",
  domain: "General",
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
        responsibilities: toList(form.responsibilities),
        preferred_skills: toList(form.preferred_skills),
        tools: toList(form.tools),
        experience_level: form.experience_level.toLowerCase(),
        domain: form.domain.toLowerCase(),
      });
      setForm(INITIAL);
    } catch (submitError) {
      setError(submitError.message || "Unable to create job right now.");
    } finally {
      setBusy(false);
    }
  }

  const handleChange = (field) => (event) => {
    setForm((prev) => ({ ...prev, [field]: event.target.value }));
  };

  return (
    <div className="space-y-4">
      <Panel
        title="Create New Job"
        subtitle="Publish job requirements with a clean, fast workflow."
      >
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            <label className="block">
              <span className="mb-1.5 block text-sm font-semibold text-slate-700">
                Title
              </span>
              <input
                value={form.title}
                onChange={handleChange("title")}
                required
                className="w-full rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-sm outline-none focus:border-brand-400 focus:ring-2 focus:ring-brand-100"
                placeholder="Senior Backend Engineer"
              />
            </label>

            <div className="grid gap-4 grid-cols-2">
              <label className="block">
                <span className="mb-1.5 block text-sm font-semibold text-slate-700">
                  Experience Level
                </span>
                <select
                  value={form.experience_level}
                  onChange={handleChange("experience_level")}
                  className="w-full rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-sm outline-none focus:border-brand-400 focus:ring-2 focus:ring-brand-100"
                >
                  {EXPERIENCE_LEVELS.map((lvl) => (
                    <option key={lvl} value={lvl}>
                      {lvl}
                    </option>
                  ))}
                </select>
              </label>

              <label className="block">
                <span className="mb-1.5 block text-sm font-semibold text-slate-700">
                  Domain
                </span>
                <select
                  value={form.domain}
                  onChange={handleChange("domain")}
                  className="w-full rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-sm outline-none focus:border-brand-400 focus:ring-2 focus:ring-brand-100"
                >
                  {DOMAINS.map((d) => (
                    <option key={d} value={d}>
                      {d}
                    </option>
                  ))}
                </select>
              </label>
            </div>
          </div>

          <label className="block">
            <span className="mb-1.5 block text-sm font-semibold text-slate-700">
              Description
            </span>
            <textarea
              rows="4"
              value={form.description}
              onChange={handleChange("description")}
              required
              className="w-full rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-sm outline-none focus:border-brand-400 focus:ring-2 focus:ring-brand-100"
              placeholder="Describe team context and outcomes."
            />
          </label>

          <label className="block">
            <span className="mb-1.5 block text-sm font-semibold text-slate-700">
              Responsibilities (one per line)
            </span>
            <textarea
              rows="3"
              value={form.responsibilities}
              onChange={handleChange("responsibilities")}
              className="w-full rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-sm outline-none focus:border-brand-400 focus:ring-2 focus:ring-brand-100"
              placeholder="Design APIs&#10;Optimize performance"
            />
          </label>

          <div className="grid gap-4 md:grid-cols-2">
            <label className="block">
              <span className="mb-1.5 block text-sm font-semibold text-slate-700">
                Required skills (comma separated)
              </span>
              <input
                value={form.skills}
                onChange={handleChange("skills")}
                className="w-full rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-sm outline-none focus:border-brand-400 focus:ring-2 focus:ring-brand-100"
                placeholder="Python, FastAPI, PostgreSQL"
              />
            </label>

            <label className="block">
              <span className="mb-1.5 block text-sm font-semibold text-slate-700">
                Preferred skills (comma separated)
              </span>
              <input
                value={form.preferred_skills}
                onChange={handleChange("preferred_skills")}
                className="w-full rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-sm outline-none focus:border-brand-400 focus:ring-2 focus:ring-brand-100"
                placeholder="Docker, Redis"
              />
            </label>
          </div>

          <label className="block">
            <span className="mb-1.5 block text-sm font-semibold text-slate-700">
              Tools (comma separated)
            </span>
            <input
              value={form.tools}
              onChange={handleChange("tools")}
              className="w-full rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-sm outline-none focus:border-brand-400 focus:ring-2 focus:ring-brand-100"
              placeholder="Jira, Git, AWS"
            />
          </label>

          <div className="flex flex-wrap gap-2">
            {toList(form.skills).map((skill) => (
              <Badge key={skill} variant="brand">
                {skill}
              </Badge>
            ))}
            {toList(form.preferred_skills).map((skill) => (
              <Badge key={skill} variant="amber">
                {skill} (Preferred)
              </Badge>
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

