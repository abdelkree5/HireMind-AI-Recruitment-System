import { EmptyState, Panel } from "../components/SaaSPrimitives";

export default function ReportsPage({ rankedCandidates }) {
  return (
    <Panel
      title="Candidate Ranking"
      subtitle="Ranked list based on match and interview signals."
    >
      {!rankedCandidates?.length ? (
        <EmptyState
          title="No ranking data"
          hint="Candidate ranking appears once applications and interviews exist."
        />
      ) : (
        <div className="space-y-2">
          {rankedCandidates.map((item, index) => (
            <article
              key={item.id}
              className="flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-slate-200 bg-white px-4 py-3"
            >
              <div>
                <p className="text-xs font-semibold uppercase tracking-wide text-brand-600">
                  Rank #{index + 1}
                </p>
                <h3 className="text-sm font-bold text-slate-900">
                  {item.candidate_name}
                </h3>
                <p className="text-xs text-slate-500">{item.job_title}</p>
              </div>

              <div className="flex gap-2 text-xs font-semibold">
                <span className="rounded-full bg-brand-100 px-2.5 py-1 text-brand-700">
                  Match {Number(item.match_score || 0).toFixed(1)}%
                </span>
                <span className="rounded-full bg-amber-100 px-2.5 py-1 text-amber-700">
                  AI {Number(item.interview_score || 0).toFixed(1)}%
                </span>
                <span className="rounded-full bg-slate-900 px-2.5 py-1 text-white">
                  Final {Number(item.final_score || 0).toFixed(1)}%
                </span>
              </div>
            </article>
          ))}
        </div>
      )}
    </Panel>
  );
}
