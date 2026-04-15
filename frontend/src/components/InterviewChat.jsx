import { useMemo, useState } from "react";
import {
  answerInterview,
  getInterviewReport,
  startInterview,
} from "../api/client";
import { Panel } from "./SaaSPrimitives";

export default function InterviewChat({ applicationId }) {
  const [sessionId, setSessionId] = useState("");
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);
  const [typing, setTyping] = useState(false);
  const [history, setHistory] = useState([
    {
      role: "assistant",
      message:
        "Hello, I am HireMind Interview AI. Start your session to begin technical evaluation.",
    },
  ]);
  const [scores, setScores] = useState({
    technical: 0,
    clarity: 0,
    experience: 0,
    final: 0,
  });

  const disabled = useMemo(() => busy || !sessionId, [busy, sessionId]);

  async function handleStart() {
    if (!applicationId) {
      setHistory((prev) => [
        ...prev,
        {
          role: "assistant",
          message: "Please provide an application ID first.",
        },
      ]);
      return;
    }

    setBusy(true);
    setTyping(true);
    try {
      const response = await startInterview(applicationId);
      setSessionId(response.session_id);
      setHistory([
        {
          role: "assistant",
          message: `Interview started. ${response.current_question || "Let's begin."}`,
        },
      ]);
    } catch {
      setHistory((prev) => [
        ...prev,
        { role: "assistant", message: "Unable to start interview right now." },
      ]);
    } finally {
      setTyping(false);
      setBusy(false);
    }
  }

  async function handleSend(event) {
    event.preventDefault();
    if (!message.trim() || !sessionId) return;

    const answer = message.trim();
    setMessage("");
    setHistory((prev) => [...prev, { role: "user", message: answer }]);

    setBusy(true);
    setTyping(true);
    try {
      const result = await answerInterview(sessionId, answer);
      setHistory((prev) => [
        ...prev,
        {
          role: "assistant",
          message: `Score ${Number(result.answer_score || 0).toFixed(1)}%: ${result.answer_feedback}`,
        },
        {
          role: "assistant",
          message: result.next_question || "Interview finished.",
        },
      ]);

      setScores((prev) => ({
        technical: Math.min(100, prev.technical + 14),
        clarity: Math.min(100, prev.clarity + 12),
        experience: Math.min(100, prev.experience + 10),
        final: Number(result.final_score || prev.final),
      }));

      if (result.is_completed) {
        const report = await getInterviewReport(sessionId);
        setScores({
          technical: Math.max(60, Number(report.overall_score || 0) - 3),
          clarity: Math.max(60, Number(report.overall_score || 0) + 1),
          experience: Math.max(60, Number(report.overall_score || 0) - 1),
          final: Number(report.overall_score || report.average_score || 0),
        });
        setHistory((prev) => [
          ...prev,
          {
            role: "assistant",
            message: `Final score: ${Number(report.overall_score || report.average_score || 0).toFixed(1)}%. Recommendation: ${report.hire_recommendation || report.recommendation}`,
          },
        ]);
      }
    } catch {
      setHistory((prev) => [
        ...prev,
        { role: "assistant", message: "Error while processing your answer." },
      ]);
    } finally {
      setTyping(false);
      setBusy(false);
    }
  }

  return (
    <div className="grid gap-4 xl:grid-cols-[1fr_280px]">
      <Panel
        title="Interview Chat"
        subtitle="Adaptive AI conversation with scoring feedback"
        actions={
          <button
            type="button"
            onClick={handleStart}
            disabled={busy || !applicationId}
            className="rounded-xl bg-brand-500 px-3 py-2 text-xs font-bold text-white transition hover:bg-brand-600 disabled:opacity-60"
          >
            Start
          </button>
        }
      >
        <div className="max-h-[420px] space-y-2 overflow-y-auto rounded-2xl bg-slate-50 p-3">
          {history.map((item, index) => (
            <div
              key={`${item.role}-${index}`}
              className={`max-w-[88%] rounded-2xl px-3 py-2 text-sm ${
                item.role === "user"
                  ? "ml-auto bg-brand-500 text-white"
                  : "bg-white text-slate-700"
              }`}
            >
              {item.message}
            </div>
          ))}
          {typing ? (
            <div className="inline-flex items-center gap-1 rounded-2xl bg-white px-3 py-2 text-sm text-slate-500">
              <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-slate-400" />
              <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-slate-400" />
              <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-slate-400" />
            </div>
          ) : null}
        </div>

        <form className="mt-3 flex gap-2" onSubmit={handleSend}>
          <input
            value={message}
            onChange={(event) => setMessage(event.target.value)}
            placeholder="Type your answer"
            disabled={busy}
            className="w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm outline-none focus:border-brand-400 focus:ring-2 focus:ring-brand-100"
          />
          <button
            type="submit"
            disabled={disabled}
            className="rounded-xl bg-slate-900 px-4 py-2 text-sm font-bold text-white transition hover:bg-slate-700 disabled:opacity-60"
          >
            Send
          </button>
        </form>
      </Panel>

      <Panel title="Score Panel" subtitle="Live interview dimensions">
        <div className="space-y-3">
          {[
            ["Technical", scores.technical],
            ["Clarity", scores.clarity],
            ["Experience", scores.experience],
            ["Final", scores.final],
          ].map(([label, value]) => (
            <div key={label}>
              <div className="mb-1 flex items-center justify-between text-xs font-semibold text-slate-600">
                <span>{label}</span>
                <span>{Number(value).toFixed(0)}%</span>
              </div>
              <div className="h-2 rounded-full bg-slate-100">
                <div
                  className="h-2 rounded-full bg-gradient-to-r from-brand-400 to-brand-600"
                  style={{ width: `${Number(value)}%` }}
                />
              </div>
            </div>
          ))}
        </div>
      </Panel>
    </div>
  );
}
