import { useState } from "react";
import CompanyDashboard from "./CompanyDashboard";

const HIRING_WORKFLOW = [
  {
    title: "Define Role",
    description:
      "Set responsibilities, must-have skills, and expected seniority.",
  },
  {
    title: "Compare Candidates",
    description:
      "Use AI ranking to compare profiles objectively against one job.",
  },
  {
    title: "Shortlist & Interview",
    description:
      "Review missing skills and start structured interview conversations.",
  },
];

function parseSkills(value) {
  return value
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
}

export default function CompanyPortal({
  onPostJob,
  postingJob,
  postMessage,
  dashboard,
  dashboardFilters,
  onDashboardFiltersChange,
}) {
  const [error, setError] = useState("");
  const totalJobs = dashboard?.total_jobs || 0;
  const totalApplications = dashboard?.total_applications || 0;
  const shortlisted =
    dashboard?.jobs?.reduce(
      (sum, item) =>
        sum +
        item.applicants.filter((app) => Number(app.match_score) >= 80).length,
      0,
    ) || 0;

  async function handlePostJob(event) {
    event.preventDefault();
    const form = event.currentTarget;
    setError("");

    const payload = {
      title: form.jobTitle.value,
      description: form.jobDescription.value,
      required_skills: parseSkills(form.requiredSkills.value),
    };

    try {
      await onPostJob(payload);
      form.reset();
    } catch (err) {
      setError("Failed to post job.");
    }
  }

  return (
    <section className="portal-stack">
      <div className="portal-intro panel">
        <h2>Company Portal</h2>
        <p>
          Manage hiring decisions with AI-assisted candidate comparison and a
          clear workflow from requisition to shortlist.
        </p>
      </div>

      <section className="stats-grid">
        <article className="stat-card panel">
          <p className="stat-label">Active Jobs</p>
          <h3>{totalJobs}</h3>
        </article>
        <article className="stat-card panel">
          <p className="stat-label">Total Applicants</p>
          <h3>{totalApplications}</h3>
        </article>
        <article className="stat-card panel">
          <p className="stat-label">Shortlisted (80%+)</p>
          <h3>{shortlisted}</h3>
        </article>
      </section>

      <section className="panel workflow-panel">
        <h3>Hiring Workflow</h3>
        <div className="workflow-grid">
          {HIRING_WORKFLOW.map((item) => (
            <article className="workflow-card" key={item.title}>
              <h4>{item.title}</h4>
              <p>{item.description}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="panel comparison-panel">
        <h3>Post New Job</h3>
        <form className="comparison-form" onSubmit={handlePostJob}>
          <label>
            Job Title
            <input
              name="jobTitle"
              placeholder="Backend Python Developer"
              required
            />
          </label>
          <label>
            Job Description
            <textarea
              name="jobDescription"
              rows="3"
              placeholder="Describe responsibilities and scope"
              required
            />
          </label>
          <label>
            Required Skills
            <input
              name="requiredSkills"
              placeholder="python, fastapi, postgresql"
            />
          </label>
          <button type="submit" disabled={postingJob}>
            {postingJob ? "Posting..." : "Post Job"}
          </button>
        </form>
        {postMessage ? <p className="apply-message">{postMessage}</p> : null}
        {error ? <p className="error-text">{error}</p> : null}
      </section>

      <CompanyDashboard
        dashboard={dashboard}
        filters={dashboardFilters}
        onChangeFilters={onDashboardFiltersChange}
      />
    </section>
  );
}
