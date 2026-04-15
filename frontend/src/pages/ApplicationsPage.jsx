import { Badge, EmptyState, Panel } from "../components/SaaSPrimitives";

function statusTone(status) {
  if (status === "accepted") return "bg-emerald-100 text-emerald-700";
  if (status === "rejected") return "bg-rose-100 text-rose-700";
  return "bg-amber-100 text-amber-700";
}

export default function ApplicationsPage({ applications }) {
  return (
    <Panel
      title="Applications"
      subtitle="Track your submitted jobs and current hiring status."
    >
      {!applications?.length ? (
        <EmptyState
          title="No applications yet"
          hint="Apply from the Jobs page and your list will appear here."
        />
      ) : (
        <div className="space-y-3">
          {applications.map((item) => (
            <article
              key={item.id}
              className="rounded-2xl border border-slate-200 bg-white p-4"
            >
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <h3 className="text-base font-bold text-slate-900">
                    {item.job_title}
                  </h3>
                  <p className="mt-1 text-xs text-slate-500">
                    Applied on {new Date(item.created_at).toLocaleDateString()}
                  </p>
                </div>
                <span
                  className={`rounded-full px-2.5 py-1 text-xs font-bold uppercase ${statusTone(item.status)}`}
                >
                  {item.status}
                </span>
              </div>

              <div className="mt-3 grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
                <Badge>
                  Match Score: {Number(item.match_score || 0).toFixed(1)}%
                </Badge>
                <Badge>
                  AI Score: {Number(item.ai_score || 0).toFixed(1)}%
                </Badge>
                <Badge>ID: {item.id}</Badge>
              </div>
            </article>
          ))}
        </div>
      )}
    </Panel>
  );
}
