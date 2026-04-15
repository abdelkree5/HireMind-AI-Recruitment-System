export default function UploadForm({ onSubmit, loading }) {
  return (
    <form className="panel form-panel" onSubmit={onSubmit}>
      <h2>Upload CV Page</h2>
      <label>
        CV File
        <input name="resumeFile" type="file" accept=".pdf,.docx" required />
      </label>
      <button type="submit" disabled={loading}>
        {loading ? "Ranking Jobs..." : "Get Job Recommendations"}
      </button>
    </form>
  );
}
