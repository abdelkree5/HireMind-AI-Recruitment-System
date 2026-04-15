import { EmptyState, Panel, StatCard } from "../components/SaaSPrimitives";

export default function CandidateDashboardPage({
  jobs,
  latestApplicationId,
  latestMatchResult,
}) {
  const matchScore = Number(latestMatchResult?.match_score || 0);
  const aiScore = Number(latestMatchResult?.ai_score || 0);

  const chartData = [
    { label: "Python", value: 84 },
    { label: "API Design", value: 76 },
    { label: "Cloud", value: 62 },
    { label: "System Design", value: 70 },
  ];

  return (
    <div className="space-y-4">
      <section className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard label="Match Score" value={`${matchScore.toFixed(1)}%`} />
        <StatCard
          label="AI Evaluation"
          value={`${aiScore.toFixed(1)}%`}
          tone="muted"
        />
        <StatCard
          label="Last CV Analysis"
          value={latestApplicationId ? "Completed" : "Pending"}
          tone="dark"
        />
        <StatCard
          label="Recommended Jobs"
          value={jobs.length || 0}
          tone="muted"
        />
      </section>

      <section className="grid gap-4 lg:grid-cols-2">
        <Panel
          title="Skills Performance"
          subtitle="Estimated profile performance by capability."
        >
          <div className="space-y-3">
            {chartData.map((item) => (
              <div key={item.label}>
                <div className="mb-1 flex items-center justify-between text-xs font-semibold text-slate-600">
                  <span>{item.label}</span>
                  <span>{item.value}%</span>
                </div>
                <div className="h-2 rounded-full bg-slate-100">
                  <div
                    className="h-2 rounded-full bg-gradient-to-r from-brand-400 to-brand-600"
                    style={{ width: `${item.value}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </Panel>

        <Panel
          title="Recent Activity"
          subtitle="Latest candidate-side actions in your portal."
        >
          {latestApplicationId ? (
            <ol className="space-y-2 text-sm text-slate-700">
              <li className="rounded-xl border border-slate-200 bg-white px-3 py-2">
                Application submitted: {latestApplicationId}
              </li>
              <li className="rounded-xl border border-slate-200 bg-white px-3 py-2">
                Match score calculated and recommendation generated.
              </li>
              <li className="rounded-xl border border-slate-200 bg-white px-3 py-2">
                Ready to continue AI interview workflow.
              </li>
            </ol>
          ) : (
            <EmptyState
              title="No activity yet"
              hint="Start from Jobs to apply and generate your first AI hiring trail."
            />
          )}
        </Panel>
      </section>
    </div>
  );
}
