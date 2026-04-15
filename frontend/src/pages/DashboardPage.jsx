import { EmptyState, Panel, StatCard } from "../components/SaaSPrimitives";

function computeShortlisted(dashboard) {
  if (!dashboard?.jobs) return 0;
  return dashboard.jobs.reduce(
    (sum, item) =>
      sum +
      item.applicants.filter((app) => Number(app.match_score || 0) >= 80)
        .length,
    0,
  );
}

export default function DashboardPage({ dashboard }) {
  const totalJobs = dashboard?.total_jobs || 0;
  const totalApplicants = dashboard?.total_applications || 0;
  const shortlisted = computeShortlisted(dashboard);
  const recent =
    (dashboard?.jobs || []).flatMap((item) =>
      (item.applicants || []).map((app) => ({
        ...app,
        jobTitle: item.job.title,
      })),
    ) || [];

  return (
    <div className="space-y-4">
      <section className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
        <StatCard label="Total Jobs" value={totalJobs} />
        <StatCard label="Applicants" value={totalApplicants} tone="muted" />
        <StatCard label="Top Candidates" value={shortlisted} tone="dark" />
      </section>

      <Panel
        title="Recent Applicants"
        subtitle="Latest pipeline updates across your open jobs."
      >
        {!recent.length ? (
          <EmptyState
            title="No applicants yet"
            hint="Share your jobs to start receiving applications."
          />
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full text-left text-sm">
              <thead>
                <tr className="text-xs uppercase tracking-wide text-slate-500">
                  <th className="pb-3 pr-3">Candidate</th>
                  <th className="pb-3 pr-3">Role</th>
                  <th className="pb-3 pr-3">Match</th>
                  <th className="pb-3">Interview</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-slate-700">
                {recent.slice(0, 6).map((item) => (
                  <tr key={item.id}>
                    <td className="py-3 pr-3 font-semibold">
                      {item.candidate_name}
                    </td>
                    <td className="py-3 pr-3">{item.jobTitle}</td>
                    <td className="py-3 pr-3">
                      {Number(item.match_score || 0).toFixed(1)}%
                    </td>
                    <td className="py-3">
                      {item.interview_status || "pending"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Panel>
    </div>
  );
}
