import {
  Badge,
  EmptyState,
  Panel,
  StatCard,
} from "../components/SaaSPrimitives";

export default function CandidateMatchingPage({ latestMatchResult }) {
  if (!latestMatchResult) {
    return (
      <Panel
        title="Job Matching"
        subtitle="Semantic matching details from your latest application."
      >
        <EmptyState
          title="No matching report yet"
          hint="Apply to a job first to see match percentage, missing skills, and recommendation panel."
        />
      </Panel>
    );
  }

  return (
    <div className="space-y-4">
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          label="Match Score"
          value={`${Number(latestMatchResult.match_score || 0).toFixed(1)}%`}
        />
        <StatCard
          label="Matched Skills"
          value={latestMatchResult.matched_skills?.length || 0}
          tone="muted"
        />
        <StatCard
          label="Missing Skills"
          value={latestMatchResult.missing_skills?.length || 0}
          tone="muted"
        />
        <StatCard label="Status" value={latestMatchResult.status} tone="dark" />
      </div>

      <Panel
        title="Matched Skills"
        subtitle="Strengths detected between your CV and the selected role."
      >
        <div className="flex flex-wrap gap-2">
          {(latestMatchResult.matched_skills || []).length ? (
            latestMatchResult.matched_skills.map((item) => (
              <Badge key={item}>{item}</Badge>
            ))
          ) : (
            <p className="text-sm text-slate-500">
              No strong overlaps found yet.
            </p>
          )}
        </div>
      </Panel>

      <Panel
        title="Missing Skills"
        subtitle="Priority skills to improve your fit."
      >
        <div className="flex flex-wrap gap-2">
          {(latestMatchResult.missing_skills || []).length ? (
            latestMatchResult.missing_skills.map((item) => (
              <Badge key={item}>{item}</Badge>
            ))
          ) : (
            <p className="text-sm text-slate-500">
              No critical missing skills detected.
            </p>
          )}
        </div>
      </Panel>

      <Panel
        title="Recommendation Panel"
        subtitle="AI explanation based on your current profile."
      >
        <p className="text-sm leading-relaxed text-slate-700">
          {latestMatchResult.recommendation ||
            "Your profile is close to the role requirements. Continue strengthening domain-specific project evidence."}
        </p>
      </Panel>
    </div>
  );
}
