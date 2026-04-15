export default function ResultsPanel({ result, rankedJobs }) {
  if (!result && (!rankedJobs || rankedJobs.length === 0)) {
    return (
      <section className="panel results-panel">
        <h2>Results Page</h2>
        <p>
          Upload a CV to see recommended job titles, ranking, missing skills,
          and score breakdown.
        </p>
      </section>
    );
  }

  const topMatch = result || rankedJobs?.[0] || null;

  return (
    <section className="panel results-panel">
      <h2>Results Page</h2>
      {topMatch ? (
        <>
          <div className="result-score">
            {topMatch.match_percentage?.toFixed?.(2) ??
              topMatch.match_percentage}
            %
          </div>
          <p>
            <strong>Top Match Score:</strong>{" "}
            {Number(topMatch.match_percentage || 0).toFixed(2)}%
          </p>
          <p>
            <strong>Top Job Title:</strong> {topMatch.job_title}
          </p>
          <p>
            <strong>Top Ranking:</strong> #{topMatch.ranking || "-"}
          </p>
          <p>
            <strong>Missing Skills (Top Match):</strong>{" "}
            {topMatch.missing_skills?.length
              ? topMatch.missing_skills.join(", ")
              : "None"}
          </p>
        </>
      ) : null}

      {rankedJobs?.length ? (
        <div className="ranking-box">
          <h3>Job Ranking</h3>
          {rankedJobs.map((job) => (
            <article
              className="rank-card"
              key={`${job.job_title}-${job.ranking || "x"}`}
            >
              <p>
                <strong>Ranking:</strong> #{job.ranking || "-"}
              </p>
              <p>
                <strong>Job:</strong> {job.job_title}
              </p>
              <p>
                <strong>Match Score:</strong>{" "}
                {Number(job.match_percentage).toFixed(2)}%
              </p>
              <p>
                <strong>Missing Skills:</strong>{" "}
                {job.missing_skills?.length
                  ? job.missing_skills.join(", ")
                  : "None"}
              </p>
              <p>
                <strong>Score Breakdown:</strong> semantic=
                {Number(job.score_breakdown?.semantic || 0).toFixed(3)} | skill=
                {Number(job.score_breakdown?.skill || 0).toFixed(3)} | title=
                {Number(job.score_breakdown?.title || 0).toFixed(3)}
              </p>
              <p>
                <strong>Feedback:</strong> {job.feedback}
              </p>
            </article>
          ))}
        </div>
      ) : null}
    </section>
  );
}
