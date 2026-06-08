import React, { useState, useEffect, useCallback } from 'react';

const API_BASE = 'http://localhost:8000';

// ─── Palette ───────────────────────────────────────────────────
const AGENT_COLORS = {
  supervisor: { bg: '#6366f1', light: '#eef2ff', label: 'Supervisor' },
  cv_analysis: { bg: '#0ea5e9', light: '#e0f2fe', label: 'CV Analysis' },
  job_analysis: { bg: '#8b5cf6', light: '#ede9fe', label: 'Job Analysis' },
  matching: { bg: '#10b981', light: '#d1fae5', label: 'Matching' },
  hiring_rules: { bg: '#f59e0b', light: '#fef3c7', label: 'Hiring Rules' },
  recruiter_feedback: { bg: '#ef4444', light: '#fee2e2', label: 'Feedback' },
  interview: { bg: '#ec4899', light: '#fce7f3', label: 'Interview' },
};

const AGENT_ORDER = [
  'supervisor', 'job_analysis', 'cv_analysis',
  'matching', 'hiring_rules', 'interview', 'recruiter_feedback',
];

// ─── Helpers ───────────────────────────────────────────────────
async function apiFetch(path, opts = {}) {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...opts,
  });
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  return res.json();
}

function Badge({ color, children }) {
  return (
    <span style={{
      background: color + '22',
      color: color,
      border: `1px solid ${color}44`,
      borderRadius: '999px',
      padding: '2px 10px',
      fontSize: '12px',
      fontWeight: 600,
      letterSpacing: '0.02em',
    }}>
      {children}
    </span>
  );
}

function Card({ children, style = {} }) {
  return (
    <div style={{
      background: '#ffffff',
      borderRadius: '16px',
      border: '1px solid #e5e7eb',
      boxShadow: '0 1px 4px rgba(0,0,0,0.06)',
      padding: '24px',
      ...style,
    }}>
      {children}
    </div>
  );
}

function MetricTile({ label, value, unit = '', color = '#6366f1' }) {
  return (
    <div style={{
      background: '#f9fafb',
      border: '1px solid #e5e7eb',
      borderRadius: '12px',
      padding: '16px 20px',
      textAlign: 'center',
      minWidth: '120px',
    }}>
      <div style={{ fontSize: '28px', fontWeight: 800, color }}>{value}{unit}</div>
      <div style={{ fontSize: '12px', color: '#6b7280', marginTop: '4px', fontWeight: 500 }}>{label}</div>
    </div>
  );
}

// ─── Agent Status Grid ─────────────────────────────────────────
function AgentStatusGrid({ errorRates, latencyStats }) {
  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(160px, 1fr))', gap: '14px' }}>
      {AGENT_ORDER.map(agent => {
        const cfg = AGENT_COLORS[agent] || { bg: '#6b7280', light: '#f3f4f6', label: agent };
        const errorRate = errorRates?.[agent];
        const latency = latencyStats?.[agent];
        const isHealthy = errorRate == null || errorRate < 0.1;

        return (
          <div key={agent} style={{
            background: cfg.light,
            border: `2px solid ${cfg.bg}33`,
            borderRadius: '14px',
            padding: '16px 14px',
            display: 'flex',
            flexDirection: 'column',
            gap: '8px',
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <div style={{
                width: '10px', height: '10px', borderRadius: '50%',
                background: isHealthy ? '#10b981' : '#ef4444',
                boxShadow: `0 0 6px ${isHealthy ? '#10b981' : '#ef4444'}`,
              }} />
              <span style={{ fontSize: '13px', fontWeight: 700, color: cfg.bg }}>{cfg.label}</span>
            </div>
            {latency && (
              <div style={{ fontSize: '11px', color: '#6b7280' }}>
                p50: {latency.p50}ms · p95: {latency.p95}ms
              </div>
            )}
            {errorRate != null && (
              <Badge color={isHealthy ? '#10b981' : '#ef4444'}>
                {isHealthy ? 'Healthy' : `${(errorRate * 100).toFixed(1)}% errors`}
              </Badge>
            )}
            {!latency && !errorRate && (
              <span style={{ fontSize: '11px', color: '#9ca3af' }}>No data yet</span>
            )}
          </div>
        );
      })}
    </div>
  );
}

// ─── Pipeline Diagram ──────────────────────────────────────────
function PipelineDiagram() {
  const steps = [
    { id: 'job_analysis', icon: '🔍' },
    { id: 'cv_analysis', icon: '📄' },
    { id: 'matching', icon: '🎯' },
    { id: 'hiring_rules', icon: '⚖️' },
    { id: 'interview', icon: '💬' },
    { id: 'recruiter_feedback', icon: '📊' },
  ];

  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '6px', flexWrap: 'wrap', padding: '12px 0' }}>
      {/* Supervisor */}
      <div style={{
        background: AGENT_COLORS.supervisor.light,
        border: `2px solid ${AGENT_COLORS.supervisor.bg}`,
        borderRadius: '10px',
        padding: '10px 14px',
        fontSize: '13px',
        fontWeight: 700,
        color: AGENT_COLORS.supervisor.bg,
        display: 'flex',
        alignItems: 'center',
        gap: '6px',
      }}>
        🧠 Supervisor
      </div>
      {steps.map((step, i) => {
        const cfg = AGENT_COLORS[step.id];
        return (
          <React.Fragment key={step.id}>
            <span style={{ color: '#9ca3af', fontSize: '18px', fontWeight: 300 }}>→</span>
            <div style={{
              background: cfg.light,
              border: `1.5px solid ${cfg.bg}66`,
              borderRadius: '10px',
              padding: '8px 12px',
              fontSize: '12px',
              fontWeight: 600,
              color: cfg.bg,
            }}>
              {step.icon} {cfg.label}
            </div>
          </React.Fragment>
        );
      })}
      <span style={{ color: '#9ca3af', fontSize: '18px' }}>→</span>
      <div style={{
        background: '#f0fdf4',
        border: '1.5px solid #10b981',
        borderRadius: '10px',
        padding: '8px 12px',
        fontSize: '12px',
        fontWeight: 700,
        color: '#10b981',
      }}>
        ✅ Final Decision
      </div>
    </div>
  );
}

// ─── Traces Table ──────────────────────────────────────────────
function TracesTable({ traces }) {
  if (!traces.length) return (
    <p style={{ color: '#9ca3af', fontSize: '14px', textAlign: 'center', padding: '24px' }}>
      No traces recorded yet. Run the agent pipeline to see execution traces.
    </p>
  );

  return (
    <div style={{ overflowX: 'auto' }}>
      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
        <thead>
          <tr style={{ background: '#f9fafb', borderBottom: '2px solid #e5e7eb' }}>
            {['Agent', 'Task', 'Status', 'Latency (ms)', 'Time'].map(h => (
              <th key={h} style={{ padding: '10px 14px', textAlign: 'left', fontWeight: 600, color: '#374151' }}>{h}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {traces.map((t, i) => {
            const cfg = AGENT_COLORS[t.agent_name] || { bg: '#6b7280' };
            const isOk = t.status === 'completed';
            return (
              <tr key={i} style={{ borderBottom: '1px solid #f3f4f6' }}>
                <td style={{ padding: '10px 14px' }}>
                  <Badge color={cfg.bg}>{t.agent_name}</Badge>
                </td>
                <td style={{ padding: '10px 14px', color: '#374151', fontFamily: 'monospace', fontSize: '12px' }}>{t.task_type}</td>
                <td style={{ padding: '10px 14px' }}>
                  <Badge color={isOk ? '#10b981' : '#ef4444'}>{t.status}</Badge>
                </td>
                <td style={{ padding: '10px 14px', color: '#6b7280' }}>{t.latency_ms?.toFixed(1) || '-'}</td>
                <td style={{ padding: '10px 14px', color: '#9ca3af', fontSize: '11px' }}>
                  {new Date(t.created_at).toLocaleTimeString()}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

// ─── Tool Registry ─────────────────────────────────────────────
function ToolRegistryPanel({ tools }) {
  if (!tools.length) return <p style={{ color: '#9ca3af' }}>No tools loaded.</p>;
  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(260px, 1fr))', gap: '12px' }}>
      {tools.map(tool => (
        <div key={tool.name} style={{
          background: tool.is_stub ? '#fafafa' : '#f0fdf4',
          border: `1.5px solid ${tool.is_stub ? '#e5e7eb' : '#10b98133'}`,
          borderRadius: '12px',
          padding: '14px 16px',
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '6px' }}>
            <span style={{ fontWeight: 700, fontSize: '13px', color: '#111827', fontFamily: 'monospace' }}>
              {tool.name}
            </span>
            {tool.is_stub
              ? <Badge color="#f59e0b">stub</Badge>
              : <Badge color="#10b981">active</Badge>
            }
          </div>
          <p style={{ fontSize: '12px', color: '#6b7280', margin: 0 }}>{tool.description}</p>
          <div style={{ marginTop: '8px' }}>
            <Badge color={tool.required_role === 'admin' ? '#ef4444' : tool.required_role === 'any' ? '#6b7280' : '#6366f1'}>
              🔒 {tool.required_role}
            </Badge>
          </div>
        </div>
      ))}
    </div>
  );
}

// ─── Metrics Panel ─────────────────────────────────────────────
function MetricsPanel({ metrics }) {
  const dq = metrics?.decision_quality || {};
  return (
    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '12px' }}>
      <MetricTile label="Total Reviews" value={dq.total || 0} color="#6366f1" />
      <MetricTile label="Agreement Rate" value={((dq.agreement_rate || 0) * 100).toFixed(1)} unit="%" color="#10b981" />
      <MetricTile label="False Positive Rate" value={((dq.false_positive_rate || 0) * 100).toFixed(1)} unit="%" color="#ef4444" />
      <MetricTile label="False Negative Rate" value={((dq.false_negative_rate || 0) * 100).toFixed(1)} unit="%" color="#f59e0b" />
      <MetricTile label="Hire Rate" value={((dq.hired_rate || 0) * 100).toFixed(1)} unit="%" color="#8b5cf6" />
    </div>
  );
}

// ─── Main Component ────────────────────────────────────────────
export default function AgentDashboardPage() {
  const [agentStatus, setAgentStatus] = useState(null);
  const [traces, setTraces] = useState([]);
  const [metrics, setMetrics] = useState(null);
  const [tools, setTools] = useState([]);
  const [semantic, setSemantic] = useState(null);
  const [activeTab, setActiveTab] = useState('pipeline');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [refreshing, setRefreshing] = useState(false);

  const fetchAll = useCallback(async () => {
    setRefreshing(true);
    try {
      const [statusData, tracesData, metricsData, toolsData] = await Promise.allSettled([
        apiFetch('/api/agents/status'),
        apiFetch('/api/agents/traces?limit=30'),
        apiFetch('/api/observability/metrics'),
        apiFetch('/api/tools?role=recruiter'),
      ]);
      if (statusData.status === 'fulfilled') setAgentStatus(statusData.value);
      if (tracesData.status === 'fulfilled') setTraces(tracesData.value);
      if (metricsData.status === 'fulfilled') setMetrics(metricsData.value);
      if (toolsData.status === 'fulfilled') setTools(toolsData.value);
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  const fetchSemantic = useCallback(async () => {
    try {
      const data = await apiFetch('/api/agents/memory/semantic');
      setSemantic(data);
    } catch (_) {}
  }, []);

  useEffect(() => {
    fetchAll();
    fetchSemantic();
    const interval = setInterval(fetchAll, 15000);
    return () => clearInterval(interval);
  }, [fetchAll, fetchSemantic]);

  const tabs = [
    { id: 'pipeline', label: '🗺 Pipeline' },
    { id: 'agents', label: '🤖 Agents' },
    { id: 'traces', label: '🔍 Traces' },
    { id: 'metrics', label: '📊 Metrics' },
    { id: 'tools', label: '🔧 Tools' },
    { id: 'memory', label: '🧠 Memory' },
  ];

  return (
    <div style={{
      minHeight: '100vh',
      background: 'linear-gradient(135deg, #f0f4ff 0%, #faf5ff 50%, #f0fdf4 100%)',
      fontFamily: "'Inter', -apple-system, sans-serif",
      padding: '32px 24px',
    }}>
      {/* Header */}
      <div style={{ maxWidth: '1400px', margin: '0 auto' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '32px' }}>
          <div>
            <h1 style={{ margin: 0, fontSize: '28px', fontWeight: 800, color: '#111827', letterSpacing: '-0.5px' }}>
              🧠 Multi-Agent Platform
            </h1>
            <p style={{ margin: '4px 0 0', color: '#6b7280', fontSize: '14px' }}>
              HireMind Production-Grade Intelligent Hiring Platform · v2.0
            </p>
          </div>
          <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
            <div style={{
              display: 'flex', alignItems: 'center', gap: '6px',
              background: '#f0fdf4', border: '1px solid #10b98166',
              borderRadius: '999px', padding: '6px 14px',
            }}>
              <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#10b981', boxShadow: '0 0 6px #10b981' }} />
              <span style={{ fontSize: '13px', fontWeight: 600, color: '#10b981' }}>Operational</span>
            </div>
            <button
              onClick={fetchAll}
              disabled={refreshing}
              style={{
                background: '#6366f1', color: '#fff', border: 'none',
                borderRadius: '10px', padding: '8px 16px', fontSize: '13px',
                fontWeight: 600, cursor: refreshing ? 'not-allowed' : 'pointer',
                opacity: refreshing ? 0.7 : 1,
              }}
            >
              {refreshing ? '⟳ Refreshing...' : '⟳ Refresh'}
            </button>
          </div>
        </div>

        {/* Tabs */}
        <div style={{ display: 'flex', gap: '8px', marginBottom: '24px', flexWrap: 'wrap' }}>
          {tabs.map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              style={{
                background: activeTab === tab.id ? '#6366f1' : '#ffffff',
                color: activeTab === tab.id ? '#ffffff' : '#374151',
                border: `1.5px solid ${activeTab === tab.id ? '#6366f1' : '#e5e7eb'}`,
                borderRadius: '10px',
                padding: '8px 16px',
                fontSize: '13px',
                fontWeight: 600,
                cursor: 'pointer',
                transition: 'all 0.15s',
              }}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Content */}
        {loading ? (
          <div style={{ textAlign: 'center', padding: '80px', color: '#6b7280' }}>
            <div style={{ fontSize: '40px', marginBottom: '16px' }}>⟳</div>
            <p>Loading agent platform data...</p>
          </div>
        ) : error ? (
          <Card style={{ borderColor: '#fca5a5', background: '#fef2f2' }}>
            <p style={{ color: '#dc2626', margin: 0 }}>⚠️ {error} — Make sure the FastAPI server is running on port 8000.</p>
          </Card>
        ) : (
          <>
            {/* PIPELINE TAB */}
            {activeTab === 'pipeline' && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
                <Card>
                  <h2 style={{ margin: '0 0 16px', fontSize: '16px', fontWeight: 700, color: '#111827' }}>
                    Agent Workflow Pipeline
                  </h2>
                  <PipelineDiagram />
                </Card>
                <Card>
                  <h2 style={{ margin: '0 0 16px', fontSize: '16px', fontWeight: 700, color: '#111827' }}>
                    Platform Metrics Overview
                  </h2>
                  <MetricsPanel metrics={metrics} />
                </Card>
              </div>
            )}

            {/* AGENTS TAB */}
            {activeTab === 'agents' && (
              <Card>
                <h2 style={{ margin: '0 0 20px', fontSize: '16px', fontWeight: 700, color: '#111827' }}>
                  Agent Registry Status
                </h2>
                <AgentStatusGrid
                  errorRates={agentStatus?.error_rates || {}}
                  latencyStats={agentStatus?.latency_stats || {}}
                />
              </Card>
            )}

            {/* TRACES TAB */}
            {activeTab === 'traces' && (
              <Card>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '16px' }}>
                  <h2 style={{ margin: 0, fontSize: '16px', fontWeight: 700, color: '#111827' }}>
                    Agent Execution Traces
                  </h2>
                  <Badge color="#6366f1">{traces.length} traces</Badge>
                </div>
                <TracesTable traces={traces} />
              </Card>
            )}

            {/* METRICS TAB */}
            {activeTab === 'metrics' && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
                <Card>
                  <h2 style={{ margin: '0 0 16px', fontSize: '16px', fontWeight: 700, color: '#111827' }}>
                    Decision Quality Metrics
                  </h2>
                  <MetricsPanel metrics={metrics} />
                </Card>
                <Card>
                  <h2 style={{ margin: '0 0 16px', fontSize: '16px', fontWeight: 700, color: '#111827' }}>
                    Agent Latency (ms)
                  </h2>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: '12px' }}>
                    {Object.entries(metrics?.latency_per_agent || {}).map(([agent, stats]) => {
                      const cfg = AGENT_COLORS[agent] || { bg: '#6b7280', label: agent };
                      return (
                        <div key={agent} style={{
                          background: '#f9fafb', border: '1px solid #e5e7eb',
                          borderRadius: '12px', padding: '14px',
                        }}>
                          <Badge color={cfg.bg}>{cfg.label || agent}</Badge>
                          <div style={{ marginTop: '10px', display: 'flex', flexDirection: 'column', gap: '4px' }}>
                            {['p50', 'p95', 'p99', 'mean'].map(k => (
                              <div key={k} style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px' }}>
                                <span style={{ color: '#9ca3af', fontWeight: 500 }}>{k}</span>
                                <span style={{ color: '#374151', fontWeight: 600 }}>{stats[k]}ms</span>
                              </div>
                            ))}
                          </div>
                        </div>
                      );
                    })}
                    {!Object.keys(metrics?.latency_per_agent || {}).length && (
                      <p style={{ color: '#9ca3af', fontSize: '14px' }}>No latency data yet — run the agent pipeline first.</p>
                    )}
                  </div>
                </Card>
              </div>
            )}

            {/* TOOLS TAB */}
            {activeTab === 'tools' && (
              <Card>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '16px' }}>
                  <h2 style={{ margin: 0, fontSize: '16px', fontWeight: 700, color: '#111827' }}>
                    MCP Tool Registry
                  </h2>
                  <Badge color="#10b981">{tools.length} tools</Badge>
                </div>
                <ToolRegistryPanel tools={tools} />
              </Card>
            )}

            {/* MEMORY TAB */}
            {activeTab === 'memory' && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
                <Card>
                  <h2 style={{ margin: '0 0 16px', fontSize: '16px', fontWeight: 700, color: '#111827' }}>
                    Semantic Memory — Domain Relations
                  </h2>
                  {semantic ? (
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(260px, 1fr))', gap: '12px' }}>
                      {Object.entries(semantic.domain_relations || {}).map(([domain, skills]) => (
                        <div key={domain} style={{
                          background: '#f9fafb', border: '1px solid #e5e7eb',
                          borderRadius: '12px', padding: '14px',
                        }}>
                          <div style={{ fontWeight: 700, fontSize: '13px', color: '#374151', marginBottom: '8px', textTransform: 'capitalize' }}>
                            📂 {domain.replace('_', ' ')}
                          </div>
                          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px' }}>
                            {skills.slice(0, 8).map(s => (
                              <span key={s} style={{
                                background: '#ede9fe', color: '#7c3aed',
                                fontSize: '11px', fontWeight: 500,
                                padding: '2px 8px', borderRadius: '999px',
                              }}>{s}</span>
                            ))}
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p style={{ color: '#9ca3af' }}>Loading semantic memory...</p>
                  )}
                </Card>
                <Card>
                  <h2 style={{ margin: '0 0 8px', fontSize: '16px', fontWeight: 700, color: '#111827' }}>
                    Memory Architecture
                  </h2>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: '12px', marginTop: '12px' }}>
                    {[
                      { name: 'Short-Term (STM)', desc: 'Active workflow context, TTL-based expiry', color: '#0ea5e9', icon: '⚡' },
                      { name: 'Long-Term (LTM)', desc: 'Recruiter preferences, hiring outcomes', color: '#8b5cf6', icon: '🏛' },
                      { name: 'Semantic', desc: 'Skills ontology, role knowledge, domain map', color: '#10b981', icon: '🧬' },
                      { name: 'Episodic', desc: 'Candidate history, recruiter interactions', color: '#f59e0b', icon: '📖' },
                    ].map(m => (
                      <div key={m.name} style={{
                        background: m.color + '11', border: `1.5px solid ${m.color}33`,
                        borderRadius: '12px', padding: '16px',
                      }}>
                        <div style={{ fontSize: '24px', marginBottom: '8px' }}>{m.icon}</div>
                        <div style={{ fontWeight: 700, fontSize: '13px', color: m.color }}>{m.name}</div>
                        <div style={{ fontSize: '12px', color: '#6b7280', marginTop: '4px' }}>{m.desc}</div>
                      </div>
                    ))}
                  </div>
                </Card>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
