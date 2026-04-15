import { useMemo, useState } from "react";
import UploadForm from "./UploadForm";
import ResultsPanel from "./ResultsPanel";
import LiveLogs from "./LiveLogs";
import InterviewChat from "./InterviewChat";
import CandidateJobBoard from "./CandidateJobBoard";
import JobDetailsPage from "./JobDetailsPage";

export default function CandidatePortal({
  onSubmit,
  loading,
  result,
  rankedJobs,
  logs,
  postedJobs,
  onApplyToJob,
  applying,
  applyMessage,
  latestApplicationId,
}) {
  const [selectedJobId, setSelectedJobId] = useState("");
  const topScore = Number(
    result?.match_percentage || rankedJobs?.[0]?.match_percentage || 0,
  ).toFixed(1);

  const selectedJob = useMemo(
    () => postedJobs.find((item) => item.id === selectedJobId) || null,
    [postedJobs, selectedJobId],
  );

  return (
    <section className="portal-stack">
      <div className="portal-intro panel">
        <h2>Candidate Portal</h2>
        <p>
          Upload your CV and instantly see recommended job titles, fit score,
          ranking, missing skills, and a full score breakdown.
        </p>
      </div>

      <section className="stats-grid">
        <article className="stat-card panel">
          <p className="stat-label">Open Jobs</p>
          <h3>{postedJobs.length}</h3>
        </article>
        <article className="stat-card panel">
          <p className="stat-label">Top Match</p>
          <h3>{topScore}%</h3>
        </article>
        <article className="stat-card panel">
          <p className="stat-label">Submitted Applications</p>
          <h3>{applyMessage ? "1+" : "0"}</h3>
        </article>
      </section>

      <section className="grid">
        <UploadForm onSubmit={onSubmit} loading={loading} />
        <ResultsPanel result={result} rankedJobs={rankedJobs} />
      </section>

      <section className="grid lower-grid">
        <LiveLogs logs={logs} />
        <InterviewChat applicationId={latestApplicationId} />
      </section>

      <section className="grid lower-grid">
        <CandidateJobBoard
          jobs={postedJobs}
          onOpenJobDetails={setSelectedJobId}
        />
      </section>

      {selectedJob ? (
        <section className="grid lower-grid">
          <JobDetailsPage
            job={selectedJob}
            onBack={() => setSelectedJobId("")}
            onApply={onApplyToJob}
            applying={applying}
            applyMessage={applyMessage}
          />
        </section>
      ) : null}
    </section>
  );
}
