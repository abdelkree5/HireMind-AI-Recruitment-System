import { useMemo, useState } from "react";
import {
  Badge,
  EmptyState,
  InlineLoader,
  Panel,
} from "../components/SaaSPrimitives";

export default function CandidateJobsPage({ jobs, onApply }) {
  const [query, setQuery] = useState("");
  const [busyJobId, setBusyJobId] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  const filteredJobs = useMemo(() => {
    const normalized = query.trim().toLowerCase();
    if (!normalized) return jobs;
    return jobs.filter((job) => {
      const haystack = [
        job.title,
        job.description,
        ...(job.required_skills || []),
        ...(job.preferred_skills || []),
      ]
        .join(" ")
        .toLowerCase();
      return haystack.includes(normalized);
    });
  }, [jobs, query]);

  async function handleApply(event, jobId) {
    event.preventDefault();
    const file = event.currentTarget.resumeFile.files?.[0];
    if (!file) return;

    const payload = new FormData();
    payload.append("file", file);

    setBusyJobId(jobId);
    setMessage("");
    setError("");

    try {
      const result = await onApply(jobId, payload);
      setMessage(
        `Applied successfully. Match score: ${Number(result.match_score || 0).toFixed(1)}%`,
      );
      event.currentTarget.reset();
    } catch (submissionError) {
      setError(submissionError.message || "Failed to apply.");
    } finally {
      setBusyJobId("");
    }
  }

  return (
    <div className="space-y-4">
      <Panel
        title="Jobs"
        subtitle="Discover open opportunities and apply with your CV."
      >
        <div className="flex flex-wrap gap-2">
          <input
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Search title, skill, keyword"
            className="w-full rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-sm outline-none focus:border-brand-400 focus:ring-2 focus:ring-brand-100 sm:w-80"
          />
          <button
            type="button"
            onClick={() => setQuery("")}
            className="rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-sm font-semibold text-slate-600"
          >
            Reset
          </button>
        </div>
        {message ? (
          <p className="mt-3 text-sm font-semibold text-emerald-700">
            {message}
          </p>
        ) : null}
        {error ? (
          <p className="mt-3 text-sm font-semibold text-rose-600">{error}</p>
        ) : null}
      </Panel>

      {!filteredJobs.length ? (
        <Panel title="Open Jobs">
          <EmptyState
            title="No jobs found"
            hint="Try another keyword or wait for new openings."
          />
        </Panel>
      ) : (
        <section className="grid gap-4 md:grid-cols-2">
          {filteredJobs.map((job) => (
            <Panel key={job.id} title={job.title} subtitle={job.description}>
              <div className="space-y-2">
                <div className="flex flex-wrap gap-2">
                  {(job.required_skills || []).map((skill) => (
                    <Badge key={skill}>{skill}</Badge>
                  ))}
                </div>

                <p className="text-xs text-slate-600">
                  <strong>Experience:</strong> {job.experience_level || "mid"} |{" "}
                  <strong>Domain:</strong> {job.domain || "general"}
                </p>

                <form
                  className="space-y-2"
                  onSubmit={(event) => handleApply(event, job.id)}
                >
                  <input
                    name="resumeFile"
                    type="file"
                    accept=".pdf,.docx"
                    required
                    className="w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm"
                  />
                  <button
                    type="submit"
                    disabled={busyJobId === job.id}
                    className="rounded-xl bg-brand-500 px-4 py-2 text-sm font-bold text-white transition hover:bg-brand-600 disabled:opacity-60"
                  >
                    {busyJobId === job.id ? "Applying..." : "Apply"}
                  </button>
                </form>

                {busyJobId === job.id ? (
                  <InlineLoader text="Submitting your CV" />
                ) : null}
              </div>
            </Panel>
          ))}
        </section>
      )}
    </div>
  );
}
