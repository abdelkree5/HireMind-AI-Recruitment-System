import { useState } from "react";

export default function JobDetailsPage({
  job,
  onBack,
  onApply,
  applying,
  applyMessage,
}) {
  const [error, setError] = useState("");

  async function handleApply(event) {
    event.preventDefault();
    const form = event.currentTarget;
    setError("");

    const formData = new FormData();
    formData.append("file", form.candidateCv.files[0]);

    try {
      await onApply(job.id, formData);
      form.reset();
    } catch (err) {
      setError(err?.message || "Could not submit application for this job.");
    }
  }

  return (
    <section className="panel job-details-page">
      <button type="button" className="text-btn" onClick={onBack}>
        ← Back to Jobs
      </button>
      <h2>{job.title}</h2>
      <p>{job.description}</p>
      <p>
        <strong>Required Skills:</strong> {job.required_skills.join(", ")}
      </p>
      <p>
        <strong>Responsibilities:</strong>{" "}
        {(job.responsibilities || []).join(" | ") || "-"}
      </p>
      <p>
        <strong>Preferred Skills:</strong>{" "}
        {(job.preferred_skills || []).join(", ") || "-"}
      </p>
      <p>
        <strong>Tools:</strong> {(job.tools || []).join(", ") || "-"}
      </p>
      <p>
        <strong>Experience:</strong> {job.experience_level || "-"} |{" "}
        <strong>Domain:</strong> {job.domain || "-"}
      </p>

      <form className="comparison-form" onSubmit={handleApply}>
        <h3>Apply Directly</h3>
        <label>
          Upload CV
          <input name="candidateCv" type="file" accept=".pdf,.docx" required />
        </label>
        <button type="submit" disabled={applying}>
          {applying ? "Submitting..." : "Apply Now"}
        </button>
      </form>

      {applyMessage ? <p className="apply-message">{applyMessage}</p> : null}
      {error ? <p className="error-text">{error}</p> : null}
    </section>
  );
}
