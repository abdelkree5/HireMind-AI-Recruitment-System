import { useState } from "react";
import { fullCvAnalysisFromCv } from "../api/client";
import {
  Badge,
  EmptyState,
  InlineLoader,
  Panel,
} from "../components/SaaSPrimitives";

export default function CandidateAnalysisPage() {
  const [busy, setBusy] = useState(false);
  const [report, setReport] = useState(null);
  const [error, setError] = useState("");

  async function handleAnalyze(event) {
    event.preventDefault();
    const file = event.currentTarget.resumeFile.files?.[0];
    if (!file) return;

    setBusy(true);
    setError("");
    setReport(null);

    try {
      const payload = new FormData();
      payload.append("file", file);
      const response = await fullCvAnalysisFromCv(payload);
      setReport(response);
    } catch {
      setError("Unable to analyze this CV right now.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-4">
      <Panel
        title="CV Analysis"
        subtitle="Upload your CV and get AI-powered profile insights."
      >
        <form className="space-y-3" onSubmit={handleAnalyze}>
          <label className="flex cursor-pointer flex-col items-center justify-center rounded-2xl border-2 border-dashed border-brand-200 bg-brand-50/50 px-4 py-10 text-center">
            <input
              name="resumeFile"
              type="file"
              accept=".pdf,.docx"
              required
              className="hidden"
            />
            <p className="text-sm font-bold text-slate-900">
              Drag & drop your CV
            </p>
            <p className="mt-1 text-xs text-slate-500">
              or click to choose PDF / DOCX
            </p>
          </label>

          <button
            type="submit"
            disabled={busy}
            className="rounded-xl bg-brand-500 px-4 py-2.5 text-sm font-bold text-white transition hover:bg-brand-600 disabled:opacity-60"
          >
            {busy ? "Analyzing..." : "Run CV Analysis"}
          </button>

          {busy ? <InlineLoader text="Running AI analysis" /> : null}
          {error ? (
            <p className="text-sm font-semibold text-rose-600">{error}</p>
          ) : null}
        </form>
      </Panel>

      {!report ? (
        <Panel title="Results" subtitle="Analysis results will appear here.">
          <EmptyState
            title="No report yet"
            hint="Upload your CV to get summary, skills, recommended roles, and gaps."
          />
        </Panel>
      ) : (
        <div className="grid gap-4 lg:grid-cols-2">
          <Panel title="Profile Summary">
            <div className="space-y-1 text-sm text-slate-700">
              <p>
                <strong>Level:</strong>{" "}
                {report.profile_summary?.candidate_level || "-"}
              </p>
              <p>
                <strong>Main domain:</strong>{" "}
                {report.profile_summary?.main_domain || "-"}
              </p>
              <p>
                <strong>Headline:</strong>{" "}
                {report.profile_summary?.inferred_headline || "-"}
              </p>
              <p>
                <strong>Description:</strong>{" "}
                {report.profile_summary?.short_description || "-"}
              </p>
            </div>
          </Panel>

          <Panel title="Skills">
            <div className="flex flex-wrap gap-2">
              {(report.profile_summary?.key_skills || []).length ? (
                report.profile_summary.key_skills.map((item) => (
                  <Badge key={item}>{item}</Badge>
                ))
              ) : (
                <p className="text-sm text-slate-500">No skills detected.</p>
              )}
            </div>
          </Panel>

          <Panel title="Recommended Roles" className="lg:col-span-2">
            <div className="grid gap-3 md:grid-cols-2">
              {(report.top_roles || []).map((role) => (
                <article
                  key={role.role_name}
                  className="rounded-2xl border border-slate-200 bg-white p-4"
                >
                  <h3 className="text-base font-bold text-slate-900">
                    {role.role_name}
                  </h3>
                  <p className="mt-1 text-xs font-semibold uppercase tracking-wide text-brand-600">
                    {role.match_level} •{" "}
                    {Number(role.confidence_score || 0).toFixed(2)}
                  </p>
                  <p className="mt-2 text-sm text-slate-600">{role.reason}</p>
                  <div className="mt-3 flex flex-wrap gap-2">
                    {(role.missing_skills || []).slice(0, 5).map((skill) => (
                      <Badge key={skill}>{skill}</Badge>
                    ))}
                  </div>
                </article>
              ))}
            </div>
          </Panel>

          <Panel title="Strengths vs Weaknesses">
            <p className="text-xs font-semibold uppercase tracking-wide text-emerald-600">
              Strengths
            </p>
            <ul className="mt-2 space-y-1 text-sm text-slate-700">
              {(report.strengths_vs_weaknesses?.strengths || []).map((item) => (
                <li key={item}>• {item}</li>
              ))}
            </ul>
          </Panel>

          <Panel title="Missing Skills (Grouped)">
            <div className="space-y-2 text-sm text-slate-700">
              {(report.top_roles || []).slice(0, 1).map((role) =>
                Object.entries(role.missing_skills_by_group || {}).map(
                  ([group, values]) => (
                    <div key={group}>
                      <p className="font-semibold text-slate-900">{group}</p>
                      <p>{values?.join(", ") || "No gaps"}</p>
                    </div>
                  ),
                ),
              )}
            </div>
          </Panel>
        </div>
      )}
    </div>
  );
}
