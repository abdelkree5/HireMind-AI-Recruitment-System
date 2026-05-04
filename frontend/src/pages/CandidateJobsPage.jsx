import { useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  Badge,
  EmptyState,
  InlineLoader,
  Panel,
  Modal,
} from "../components/SaaSPrimitives";

export default function CandidateJobsPage({ jobs, onApply, onPreMatch }) {
  const navigate = useNavigate();
  const [query, setQuery] = useState("");
  const [busyJobId, setBusyJobId] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  // Pre-match state
  const [preMatch, setPreMatch] = useState(null);
  const [selectedFile, setSelectedFile] = useState(null);
  const [confirmedSkills, setConfirmedSkills] = useState([]);

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

  async function handleFileSelect(event, jobId) {
    const file = event.target.files?.[0];
    if (!file) return;

    setSelectedFile(file);
    setBusyJobId(jobId);
    setError("");

    const payload = new FormData();
    payload.append("file", file);

    try {
      const result = await onPreMatch(jobId, payload);
      setPreMatch({ ...result, jobId });
      setConfirmedSkills(result.matched_skills || []);
    } catch (err) {
      setError(err.message || "Failed to analyze CV.");
    } finally {
      setBusyJobId("");
    }
  }

  async function handleFinalApply() {
    if (!selectedFile || !preMatch) return;

    const jobId = preMatch.jobId;
    const payload = new FormData();
    payload.append("file", selectedFile);
    payload.append("confirmed_skills", JSON.stringify(confirmedSkills));

    setBusyJobId(jobId);
    setPreMatch(null);
    setMessage("");
    setError("");

    try {
      await onApply(jobId, payload);
      // Success - Redirect to interview
      navigate("/candidate/interview");
    } catch (submissionError) {
      setError(submissionError.message || "Failed to apply.");
    } finally {
      setBusyJobId("");
    }
  }

  const toggleSkill = (skill) => {
    setConfirmedSkills((prev) =>
      prev.includes(skill) ? prev.filter((s) => s !== skill) : [...prev, skill],
    );
  };

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

                <div className="space-y-2">
                  <label className="block">
                    <span className="mb-1 block text-[10px] font-bold uppercase tracking-wider text-slate-400">
                      Upload Resume to Match
                    </span>
                    <input
                      type="file"
                      accept=".pdf,.docx"
                      onChange={(e) => handleFileSelect(e, job.id)}
                      className="w-full text-xs text-slate-500 file:mr-4 file:rounded-lg file:border-0 file:bg-slate-100 file:px-4 file:py-2 file:text-xs file:font-bold file:text-slate-700 hover:file:bg-slate-200"
                    />
                  </label>
                </div>

                {busyJobId === job.id && !preMatch ? (
                  <InlineLoader text="Analyzing CV Compatibility..." />
                ) : null}
              </div>
            </Panel>
          ))}
        </section>
      )}

      {/* Pre-match Modal */}
      <Modal
        open={Boolean(preMatch)}
        title="AI Match Analysis"
        description="Verify how your skills align with the role requirements before applying."
        onCancel={() => setPreMatch(null)}
        onConfirm={handleFinalApply}
        confirmText="Confirm & Apply"
      >
        {preMatch && (
          <div className="space-y-6 py-4">
            <div className="flex items-center justify-between rounded-2xl bg-slate-50 p-4">
              <div>
                <p className="text-xs font-bold uppercase tracking-widest text-slate-400">
                  Overall Match
                </p>
                <h3 className="text-2xl font-black text-slate-900">
                  {preMatch.score}%
                </h3>
              </div>
              <Badge
                variant={preMatch.score > 70 ? "success" : "brand"}
                className="px-4 py-2 text-lg"
              >
                {preMatch.match_level}
              </Badge>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="rounded-xl border border-slate-100 p-3">
                <p className="text-[10px] font-bold text-slate-400">
                  INFERRED LEVEL
                </p>
                <p className="text-sm font-bold text-slate-700 capitalize">
                  {preMatch.candidate_level}
                </p>
              </div>
              <div className="rounded-xl border border-slate-100 p-3">
                <p className="text-[10px] font-bold text-slate-400">
                  MAIN DOMAIN
                </p>
                <p className="text-sm font-bold text-slate-700 capitalize">
                  {preMatch.candidate_domain}
                </p>
              </div>
            </div>

            <div className="space-y-3">
              <p className="text-xs font-bold text-slate-700">
                Skills Verification
              </p>
              <div className="max-h-48 space-y-2 overflow-y-auto pr-2">
                {preMatch.job_required_skills.map((skill) => (
                  <label
                    key={skill}
                    className="flex cursor-pointer items-center gap-3 rounded-lg border border-slate-100 p-2.5 transition hover:bg-slate-50"
                  >
                    <input
                      type="checkbox"
                      checked={confirmedSkills.includes(skill)}
                      onChange={() => toggleSkill(skill)}
                      className="h-4 w-4 rounded border-slate-300 text-brand-600 focus:ring-brand-500"
                    />
                    <span className="text-sm font-medium text-slate-700">
                      {skill}
                    </span>
                    {preMatch.matched_skills.includes(skill) && (
                      <span className="ml-auto text-[10px] font-bold text-emerald-600">
                        Extracted from CV
                      </span>
                    )}
                  </label>
                ))}
              </div>
            </div>

            <p className="text-[10px] italic text-slate-500">
              * The AI has pre-selected skills found in your CV. You can
              manually confirm others if applicable.
            </p>
          </div>
        )}
      </Modal>
    </div>
  );
}
