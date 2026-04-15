import { useState } from "react";
import InterviewChat from "../components/InterviewChat";
import { Panel, StatCard } from "../components/SaaSPrimitives";

export default function CandidateInterviewPage({ latestApplicationId }) {
  const [applicationId, setApplicationId] = useState(latestApplicationId || "");

  return (
    <div className="space-y-4">
      <section className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard label="Technical Depth" value="78%" tone="muted" />
        <StatCard label="Clarity" value="81%" tone="muted" />
        <StatCard label="Experience" value="74%" tone="muted" />
        <StatCard label="Final Score" value="77%" tone="dark" />
      </section>

      <Panel
        title="AI Interview"
        subtitle="Paste an application ID to start a structured adaptive interview."
      >
        <input
          value={applicationId}
          onChange={(event) => setApplicationId(event.target.value)}
          placeholder="Application ID"
          className="w-full rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-sm outline-none focus:border-brand-400 focus:ring-2 focus:ring-brand-100"
        />
      </Panel>

      <InterviewChat applicationId={applicationId} />
    </div>
  );
}
