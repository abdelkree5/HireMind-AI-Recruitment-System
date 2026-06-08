import { useState } from "react";
import { EmptyState, Panel, Badge } from "../components/SaaSPrimitives";
import { submitRecruiterFeedback } from "../api/client";

function flattenApplicants(dashboard) {
  const jobs = dashboard?.jobs || [];
  return jobs.flatMap((jobItem) =>
    (jobItem.applicants || []).map((applicant) => ({
      ...applicant,
      job_title: jobItem.job.title,
    })),
  );
}

export default function ApplicantsPage({ dashboard, onDataChanged }) {
  const applicants = flattenApplicants(dashboard);
  const [selectedApplicant, setSelectedApplicant] = useState(null);
  const [decision, setDecision] = useState("ACCEPTED");
  const [notes, setNotes] = useState("");
  const [rejectionReason, setRejectionReason] = useState("");
  const [submitting, setSubmitting] = useState(false);

  async function handleReviewSubmit(e) {
    e.preventDefault();
    if (!selectedApplicant) return;

    setSubmitting(true);
    try {
      await submitRecruiterFeedback({
        application_id: selectedApplicant.id,
        job_id: selectedApplicant.job_id,
        ai_score: Number(selectedApplicant.match_score || 0),
        candidate_rank: selectedApplicant.ranking || 1,
        recruiter_decision: decision,
        recruiter_notes: notes,
        rejection_reason: decision === "REJECTED" ? rejectionReason : "",
        candidate_id: selectedApplicant.candidate_name,
      });

      setSelectedApplicant(null);
      setNotes("");
      setRejectionReason("");
      onDataChanged?.();
    } catch (err) {
      alert("Failed to save review: " + err.message);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="space-y-6">
      <Panel
        title="Applicants Pipeline"
        subtitle="Review candidate match, AI interview scores, and submit recruiter feedback."
      >
        {!applicants.length ? (
          <EmptyState
            title="No applicants yet"
            hint="Once candidates apply, they will appear in this table."
          />
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full text-left text-sm">
              <thead>
                <tr className="text-xs uppercase tracking-wide text-slate-500">
                  <th className="pb-3 pr-3">Candidate name</th>
                  <th className="pb-3 pr-3">Role</th>
                  <th className="pb-3 pr-3">Match score</th>
                  <th className="pb-3 pr-3">AI Score</th>
                  <th className="pb-3">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-slate-700">
                {applicants.map((item) => (
                  <tr key={item.id} className="hover:bg-slate-50/50">
                    <td className="py-3 pr-3 font-semibold">
                      {item.candidate_name}
                    </td>
                    <td className="py-3 pr-3">{item.job_title}</td>
                    <td className="py-3 pr-3">
                      <span className="font-bold text-slate-900">
                        {Number(item.match_score || 0).toFixed(1)}%
                      </span>
                    </td>
                    <td className="py-3 pr-3">
                      {item.interview_score !== null ? (
                        <span className="font-bold text-emerald-600">
                          {Number(item.interview_score).toFixed(1)}%
                        </span>
                      ) : (
                        <span className="text-slate-400 text-xs">No Interview</span>
                      )}
                    </td>
                    <td className="py-3 space-x-2">
                      <button
                        type="button"
                        onClick={() => {
                          setSelectedApplicant(item);
                          setDecision("ACCEPTED");
                        }}
                        className="rounded-xl border border-slate-200 bg-white px-3 py-1.5 text-xs font-bold text-slate-600 hover:bg-slate-50"
                      >
                        Review Decision
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Panel>

      {selectedApplicant && (
        <Panel
          title={`Review Application: ${selectedApplicant.candidate_name}`}
          subtitle={`Submit hiring team decision for ${selectedApplicant.job_title}`}
        >
          <form onSubmit={handleReviewSubmit} className="space-y-4 max-w-xl">
            <div className="grid gap-2">
              <label className="text-xs font-bold uppercase tracking-wider text-slate-500">
                Recruiter Decision
              </label>
              <select
                value={decision}
                onChange={(e) => setDecision(e.target.value)}
                className="w-full rounded-2xl border border-slate-200 bg-white p-3 text-sm focus:border-slate-400 focus:outline-none"
              >
                <option value="ACCEPTED">Accept / Shortlist</option>
                <option value="INTERVIEWED">Schedule Interview</option>
                <option value="HIRED">Hire Candidate</option>
                <option value="REJECTED">Reject</option>
              </select>
            </div>

            {decision === "REJECTED" && (
              <div className="grid gap-2">
                <label className="text-xs font-bold uppercase tracking-wider text-slate-500">
                  Rejection Reason
                </label>
                <select
                  value={rejectionReason}
                  onChange={(e) => setRejectionReason(e.target.value)}
                  className="w-full rounded-2xl border border-slate-200 bg-white p-3 text-sm focus:border-slate-400 focus:outline-none"
                  required
                >
                  <option value="">Select a reason...</option>
                  <option value="Missing mandatory skills">Missing mandatory skills</option>
                  <option value="Experience below requirement">Experience below requirement</option>
                  <option value="Seniority mismatch">Seniority mismatch</option>
                  <option value="Education level not met">Education level not met</option>
                  <option value="Salary expectations too high">Salary expectations too high</option>
                  <option value="Work authorization required">Work authorization required</option>
                  <option value="Other">Other</option>
                </select>
              </div>
            )}

            <div className="grid gap-2">
              <label className="text-xs font-bold uppercase tracking-wider text-slate-500">
                Hiring Notes
              </label>
              <textarea
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                rows={4}
                placeholder="Include details about skill alignment or interview performance..."
                className="w-full rounded-2xl border border-slate-200 p-3 text-sm focus:border-slate-400 focus:outline-none"
              />
            </div>

            <div className="flex gap-2 justify-end">
              <button
                type="button"
                onClick={() => setSelectedApplicant(null)}
                className="rounded-xl border border-slate-200 bg-white px-4 py-2 text-xs font-bold text-slate-600 hover:bg-slate-50"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={submitting}
                className="rounded-xl bg-slate-900 px-4 py-2 text-xs font-bold text-white hover:bg-slate-800 disabled:opacity-50"
              >
                {submitting ? "Submitting..." : "Submit Review"}
              </button>
            </div>
          </form>
        </Panel>
      )}
    </div>
  );
}
