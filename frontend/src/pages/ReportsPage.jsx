import { useState, useEffect } from "react";
import { EmptyState, Panel } from "../components/SaaSPrimitives";
import { getFeedbackAnalytics, getLtrInfo, trainLtrModel } from "../api/client";

export default function ReportsPage({ rankedCandidates }) {
  const [analytics, setAnalytics] = useState(null);
  const [ltrInfo, setLtrInfo] = useState(null);
  const [loading, setLoading] = useState(false);
  const [training, setTraining] = useState(false);

  async function loadData() {
    setLoading(true);
    try {
      const [anaRes, ltrRes] = await Promise.all([
        getFeedbackAnalytics(),
        getLtrInfo()
      ]);
      setAnalytics(anaRes);
      setLtrInfo(ltrRes);
    } catch (err) {
      console.error("Failed to load reports analytics:", err);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadData();
  }, []);

  async function handleRetrain() {
    setTraining(true);
    try {
      const res = await trainLtrModel();
      if (res.status === "success") {
        alert("Learning-to-Rank (LTR) model retrained successfully!");
        loadData();
      } else {
        alert("Retraining failed: " + res.message);
      }
    } catch (err) {
      alert("Error retraining: " + err.message);
    } finally {
      setTraining(false);
    }
  }

  return (
    <div className="space-y-6">
      {/* 1. LTR Ranker Control panel */}
      <Panel
        title="Learning-to-Rank (LTR) Model Control"
        subtitle="Train and manage the machine learning ranker dynamically using recruiter actions."
      >
        <div className="grid gap-6 md:grid-cols-2">
          <div className="space-y-4">
            <div className="rounded-2xl border border-slate-200 bg-white p-4 space-y-3">
              <h3 className="font-bold text-sm text-slate-800">Model Status</h3>
              <div className="grid grid-cols-2 gap-2 text-xs">
                <span className="text-slate-500">Status:</span>
                <span className="font-semibold text-slate-900 capitalize">
                  {ltrInfo?.status || "not_trained"}
                </span>
                <span className="text-slate-500">Algorithm:</span>
                <span className="font-semibold text-slate-900">
                  {ltrInfo?.metadata?.trained_with || "N/A"}
                </span>
                <span className="text-slate-500">Version:</span>
                <span className="font-semibold text-slate-900">
                  {ltrInfo?.metadata?.version || "N/A"}
                </span>
                <span className="text-slate-500">Training Samples:</span>
                <span className="font-semibold text-slate-900">
                  {ltrInfo?.metadata?.samples_count || 0} applications
                </span>
              </div>
              
              <button
                type="button"
                disabled={training}
                onClick={handleRetrain}
                className="w-full rounded-xl bg-slate-900 px-3 py-2 text-xs font-bold text-white hover:bg-slate-800 disabled:opacity-50"
              >
                {training ? "Retraining Model..." : "Retrain LTR Ranker"}
              </button>
            </div>
          </div>

          <div className="space-y-3 rounded-2xl border border-slate-200 bg-white p-4">
            <h3 className="font-bold text-sm text-slate-800">Feature Importance Weights</h3>
            {ltrInfo?.metadata?.feature_importance ? (
              <div className="space-y-2 text-xs">
                {Object.entries(ltrInfo.metadata.feature_importance)
                  .sort((a, b) => b[1] - a[1])
                  .slice(0, 6)
                  .map(([feature, val]) => (
                    <div key={feature} className="space-y-1">
                      <div className="flex justify-between text-[11px] text-slate-600">
                        <span className="capitalize">{feature.replace(/_/g, " ")}</span>
                        <span>{val.toFixed(1)}</span>
                      </div>
                      <div className="h-1.5 w-full rounded-full bg-slate-100">
                        <div
                          className="h-full rounded-full bg-slate-800 transition-all"
                          style={{ width: `${Math.min(100, (val / 10) * 100)}%` }}
                        />
                      </div>
                    </div>
                  ))}
              </div>
            ) : (
              <p className="text-xs text-slate-400">Model has not been trained yet. Train the model to see feature importances.</p>
            )}
          </div>
        </div>
      </Panel>

      {/* 2. Analytics & Observability Dashboard */}
      {analytics && (
        <Panel
          title="Recruiter Observability Dashboard"
          subtitle="Real-time agreement metrics and alignment between recruiter feedback and AI scoring."
        >
          <div className="grid gap-3 sm:grid-cols-3 mb-6">
            <div className="rounded-2xl border border-slate-200 bg-white p-4">
              <p className="text-xs font-semibold text-slate-500 uppercase">Agreement Rate</p>
              <p className="mt-1 text-2xl font-black text-slate-900">
                {(analytics.recruiter_ai_agreement_rate * 100).toFixed(1)}%
              </p>
            </div>
            <div className="rounded-2xl border border-slate-200 bg-white p-4">
              <p className="text-xs font-semibold text-slate-500 uppercase">Conversion Rate</p>
              <p className="mt-1 text-2xl font-black text-slate-900">
                {(analytics.hiring_conversion_rate * 100).toFixed(1)}%
              </p>
            </div>
            <div className="rounded-2xl border border-slate-200 bg-white p-4">
              <p className="text-xs font-semibold text-slate-500 uppercase">Acceptance Rate</p>
              <p className="mt-1 text-2xl font-black text-slate-900">
                {(analytics.acceptance_rate * 100).toFixed(1)}%
              </p>
            </div>
          </div>

          <div className="grid gap-6 md:grid-cols-2">
            <div className="space-y-2">
              <h4 className="text-xs font-bold text-slate-500 uppercase">Top Rejection Reasons</h4>
              {Object.keys(analytics.most_common_rejection_reasons).length > 0 ? (
                <ul className="divide-y divide-slate-100 rounded-2xl border border-slate-200 bg-white px-4 py-1 text-xs">
                  {Object.entries(analytics.most_common_rejection_reasons).map(([reason, count]) => (
                    <li key={reason} className="py-2 flex justify-between">
                      <span className="text-slate-700">{reason}</span>
                      <span className="font-semibold text-slate-950">{count} rejections</span>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="text-xs text-slate-400">No rejection feedback captured yet.</p>
              )}
            </div>

            <div className="space-y-2">
              <h4 className="text-xs font-bold text-slate-500 uppercase">False Positives (AI High, Rejected)</h4>
              {analytics.false_positives.length > 0 ? (
                <div className="space-y-2">
                  {analytics.false_positives.slice(0, 3).map((fp) => (
                    <div key={fp.application_id} className="rounded-2xl border border-slate-200 bg-white p-3 text-xs">
                      <div className="flex justify-between font-bold text-slate-800">
                        <span>{fp.candidate_name}</span>
                        <span className="text-rose-600">AI Score: {fp.ai_score}%</span>
                      </div>
                      <p className="mt-1 text-slate-500 font-semibold">Reason: {fp.rejection_reason || "None specified"}</p>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-xs text-slate-400">No false positive discrepancies detected.</p>
              )}
            </div>
          </div>
        </Panel>
      )}

      {/* 3. Candidate Rankings */}
      <Panel
        title="Candidate LTR Ranking List"
        subtitle="Combined rankings incorporating retrieval matches, interview, and LTR machine-learned priority scoring."
      >
        {!rankedCandidates?.length ? (
          <EmptyState
            title="No ranking data"
            hint="Candidate ranking appears once applications and interviews exist."
          />
        ) : (
          <div className="space-y-2">
            {rankedCandidates.map((item, index) => (
              <article
                key={item.id}
                className="flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-slate-200 bg-white px-4 py-3"
              >
                <div>
                  <p className="text-xs font-semibold uppercase tracking-wide text-brand-600">
                    Rank #{index + 1}
                  </p>
                  <h3 className="text-sm font-bold text-slate-900">
                    {item.candidate_name}
                  </h3>
                  <p className="text-xs text-slate-500">{item.job_title}</p>
                </div>

                <div className="flex gap-2 text-xs font-semibold">
                  <span className="rounded-full bg-brand-100 px-2.5 py-1 text-brand-700">
                    Match {Number(item.match_score || 0).toFixed(1)}%
                  </span>
                  <span className="rounded-full bg-amber-100 px-2.5 py-1 text-amber-700">
                    AI {Number(item.interview_score || 0).toFixed(1)}%
                  </span>
                  <span className="rounded-full bg-slate-900 px-2.5 py-1 text-white">
                    Final {Number(item.final_score || 0).toFixed(1)}%
                  </span>
                </div>
              </article>
            ))}
          </div>
        )}
      </Panel>
    </div>
  );
}
