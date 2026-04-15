import { useState } from "react";

export default function CandidateJobBoard({ jobs, onOpenJobDetails }) {
  const [selectedJobId, setSelectedJobId] = useState("");

  function handleOpen(event) {
    event.preventDefault();
    const chosenJobId = selectedJobId || jobs?.[0]?.id;
    if (!chosenJobId) return;
    onOpenJobDetails(chosenJobId);
  }

  return (
    <section className="panel candidate-jobs-panel">
      <h2>Open Jobs</h2>
      {jobs?.length ? (
        <div className="open-jobs-grid">
          {jobs.map((job) => (
            <article className="rank-card" key={job.id}>
              <p>
                <strong>{job.title}</strong>
              </p>
              <p>{job.description}</p>
              <p>
                <strong>Required Skills:</strong>{" "}
                {job.required_skills.join(", ")}
              </p>
              <button
                type="button"
                className="inline-btn"
                onClick={() => onOpenJobDetails(job.id)}
              >
                View Job Page & Apply
              </button>
            </article>
          ))}
        </div>
      ) : (
        <p>No jobs posted yet.</p>
      )}

      <form className="comparison-form" onSubmit={handleOpen}>
        <h3>Go to Job Page</h3>
        <label>
          Select Job
          <select
            value={selectedJobId}
            onChange={(event) => setSelectedJobId(event.target.value)}
            required
          >
            <option value="">Choose a job</option>
            {jobs.map((job) => (
              <option key={job.id} value={job.id}>
                {job.title}
              </option>
            ))}
          </select>
        </label>
        <button type="submit">Open Job Details</button>
      </form>
    </section>
  );
}
