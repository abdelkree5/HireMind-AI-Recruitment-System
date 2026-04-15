import { useState } from "react";
import {
  Badge,
  EmptyState,
  InlineLoader,
  Modal,
  Panel,
} from "../components/SaaSPrimitives";

function parseSkills(input) {
  return input
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
}

export default function JobsPage({
  jobs,
  onUpdateJob,
  onDeleteJob,
  onSeedJobs,
}) {
  const [editingId, setEditingId] = useState("");
  const [deleteId, setDeleteId] = useState("");
  const [skillsInput, setSkillsInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function handleSeed() {
    setBusy(true);
    setError("");
    try {
      await onSeedJobs();
    } catch (seedError) {
      setError(seedError.message || "Unable to seed jobs.");
    } finally {
      setBusy(false);
    }
  }

  async function handleUpdate(job) {
    setBusy(true);
    setError("");
    try {
      await onUpdateJob(job.id, {
        title: job.title,
        description: job.description,
        required_skills: parseSkills(
          skillsInput || job.required_skills.join(", "),
        ),
      });
      setEditingId("");
      setSkillsInput("");
    } catch (updateError) {
      setError(updateError.message || "Update failed.");
    } finally {
      setBusy(false);
    }
  }

  async function handleDelete(jobId) {
    setBusy(true);
    setError("");
    try {
      await onDeleteJob(jobId);
      setDeleteId("");
    } catch (deleteError) {
      setError(deleteError.message || "Delete failed.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-4">
      <Panel
        title="Jobs List"
        subtitle="Manage all posted roles, edit skills, and control job lifecycle."
        actions={
          <button
            type="button"
            onClick={handleSeed}
            disabled={busy}
            className="rounded-xl bg-brand-500 px-3 py-2 text-xs font-bold text-white transition hover:bg-brand-600 disabled:opacity-60"
          >
            Seed 10 Realistic Jobs
          </button>
        }
      >
        {busy ? <InlineLoader text="Applying changes" /> : null}
        {error ? (
          <p className="mt-2 text-sm font-semibold text-rose-600">{error}</p>
        ) : null}
      </Panel>

      {!jobs?.length ? (
        <Panel title="Open Roles">
          <EmptyState
            title="No jobs posted"
            hint="Create a role from Add Job page."
          />
        </Panel>
      ) : (
        <section className="grid gap-4 md:grid-cols-2">
          {jobs.map((job) => (
            <Panel key={job.id} title={job.title} subtitle={job.description}>
              <div className="space-y-2">
                <div className="flex flex-wrap gap-2">
                  {(job.required_skills || []).map((skill) => (
                    <Badge key={skill}>{skill}</Badge>
                  ))}
                </div>

                {editingId === job.id ? (
                  <div className="space-y-2">
                    <input
                      value={skillsInput}
                      onChange={(event) => setSkillsInput(event.target.value)}
                      placeholder="comma separated skills"
                      className="w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm outline-none focus:border-brand-400 focus:ring-2 focus:ring-brand-100"
                    />
                    <div className="flex gap-2">
                      <button
                        type="button"
                        onClick={() => handleUpdate(job)}
                        className="rounded-xl bg-slate-900 px-3 py-2 text-xs font-bold text-white"
                      >
                        Save
                      </button>
                      <button
                        type="button"
                        onClick={() => {
                          setEditingId("");
                          setSkillsInput("");
                        }}
                        className="rounded-xl border border-slate-200 bg-white px-3 py-2 text-xs font-bold text-slate-600"
                      >
                        Cancel
                      </button>
                    </div>
                  </div>
                ) : (
                  <div className="flex gap-2">
                    <button
                      type="button"
                      onClick={() => {
                        setEditingId(job.id);
                        setSkillsInput(job.required_skills.join(", "));
                      }}
                      className="rounded-xl bg-amber-100 px-3 py-2 text-xs font-bold text-amber-800"
                    >
                      Edit
                    </button>
                    <button
                      type="button"
                      onClick={() => setDeleteId(job.id)}
                      className="rounded-xl bg-rose-100 px-3 py-2 text-xs font-bold text-rose-700"
                    >
                      Delete
                    </button>
                  </div>
                )}
              </div>
            </Panel>
          ))}
        </section>
      )}

      <Modal
        open={Boolean(deleteId)}
        title="Delete job"
        description="This will remove the role and related application records."
        onCancel={() => setDeleteId("")}
        onConfirm={() => handleDelete(deleteId)}
      />
    </div>
  );
}
