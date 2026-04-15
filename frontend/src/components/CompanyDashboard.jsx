export default function CompanyDashboard({
  dashboard,
  filters,
  onChangeFilters,
}) {
  if (!dashboard) {
    return null;
  }

  function updateFilters(patch) {
    onChangeFilters({ ...filters, ...patch });
  }

  return (
    <section className="panel workflow-panel">
      <h3>Applications Dashboard</h3>
      <div className="dashboard-controls">
        <label>
          Sort By
          <select
            value={filters.sort_by}
            onChange={(event) => updateFilters({ sort_by: event.target.value })}
          >
            <option value="score">Score</option>
            <option value="date">Date</option>
          </select>
        </label>
        <label>
          Order
          <select
            value={filters.order}
            onChange={(event) => updateFilters({ order: event.target.value })}
          >
            <option value="desc">Descending</option>
            <option value="asc">Ascending</option>
          </select>
        </label>
        <label>
          Min Score
          <input
            type="number"
            min="0"
            max="100"
            value={filters.min_score}
            onChange={(event) =>
              updateFilters({ min_score: event.target.value })
            }
            placeholder="e.g. 60"
          />
        </label>
        <label>
          Since Date
          <input
            type="date"
            value={filters.since_date}
            onChange={(event) =>
              updateFilters({ since_date: event.target.value })
            }
          />
        </label>
      </div>
      <p>
        <strong>Total Jobs:</strong> {dashboard.total_jobs} |{" "}
        <strong>Total Applications:</strong> {dashboard.total_applications}
      </p>

      <div className="open-jobs-grid">
        {dashboard.jobs.map((item) => (
          <article className="rank-card" key={item.job.id}>
            <p>
              <strong>{item.job.title}</strong>
            </p>
            <p>{item.job.description}</p>
            <p>
              <strong>Applicants:</strong> {item.applicants.length}
            </p>
            {item.applicants.length ? (
              <div className="applicants-list">
                {item.applicants.map((applicant) => (
                  <div key={applicant.id} className="applicant-item">
                    <p>
                      <strong>{applicant.candidate_name}</strong> -{" "}
                      {applicant.candidate_headline}
                    </p>
                    <p>
                      Match: {Number(applicant.match_score).toFixed(2)}% |
                      Missing: {applicant.missing_skills.join(", ") || "None"}
                    </p>
                    <p>
                      Interview: {applicant.interview_status || "not_started"} |
                      Score:{" "}
                      {applicant.interview_score != null
                        ? `${Number(applicant.interview_score).toFixed(1)}%`
                        : "-"}
                    </p>
                  </div>
                ))}
              </div>
            ) : (
              <p>No applicants yet.</p>
            )}
          </article>
        ))}
      </div>
    </section>
  );
}
