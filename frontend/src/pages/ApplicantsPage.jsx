import { EmptyState, Panel } from "../components/SaaSPrimitives";

function flattenApplicants(dashboard) {
  const jobs = dashboard?.jobs || [];
  return jobs.flatMap((jobItem) =>
    (jobItem.applicants || []).map((applicant) => ({
      ...applicant,
      job_title: jobItem.job.title,
    })),
  );
}

export default function ApplicantsPage({ dashboard }) {
  const applicants = flattenApplicants(dashboard);

  return (
    <Panel
      title="Applicants"
      subtitle="Review candidate match and AI interview scores."
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
                <th className="pb-3 pr-3">AI score</th>
                <th className="pb-3">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-slate-700">
              {applicants.map((item) => (
                <tr key={item.id}>
                  <td className="py-3 pr-3 font-semibold">
                    {item.candidate_name}
                  </td>
                  <td className="py-3 pr-3">{item.job_title}</td>
                  <td className="py-3 pr-3">
                    {Number(item.match_score || 0).toFixed(1)}%
                  </td>
                  <td className="py-3 pr-3">
                    {Number(item.interview_score || 0).toFixed(1)}%
                  </td>
                  <td className="py-3">
                    <button
                      type="button"
                      className="rounded-xl border border-slate-200 bg-white px-3 py-1.5 text-xs font-bold text-slate-600"
                    >
                      View CV
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </Panel>
  );
}
