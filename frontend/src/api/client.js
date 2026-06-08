const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";
const AUTH_STORAGE_KEY = "hiremind.auth";

export function getStoredAuthSession() {
  if (typeof localStorage === "undefined") return null;
  try {
    const raw = localStorage.getItem(AUTH_STORAGE_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

export function setStoredAuthSession(session) {
  if (typeof localStorage === "undefined") return;
  localStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify(session));
}

export function clearStoredAuthSession() {
  if (typeof localStorage === "undefined") return;
  localStorage.removeItem(AUTH_STORAGE_KEY);
}

function cloneFormData(source) {
  const copy = new FormData();
  for (const [key, value] of source.entries()) {
    copy.append(key, value);
  }
  return copy;
}

export async function analyzeResume(formData) {
  const response = await fetch(`${API_BASE}/api/cv/analyze`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    throw new Error("Failed to analyze CV.");
  }

  return response.json();
}

export async function analyzeResumeStream(formData, onEvent) {
  const response = await fetch(`${API_BASE}/api/cv/analyze/stream`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok || !response.body) {
    throw new Error("Failed to start live analysis.");
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder("utf-8");
  let buffer = "";
  let finalResult = null;

  while (true) {
    const { value, done } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const chunks = buffer.split("\n\n");
    buffer = chunks.pop() || "";

    for (const chunk of chunks) {
      const line = chunk
        .split("\n")
        .find((entry) => entry.startsWith("data: "));
      if (!line) continue;

      const payload = JSON.parse(line.replace(/^data: /, ""));
      onEvent?.(payload);
      if (payload.type === "result") {
        finalResult = payload;
      }
    }
  }

  return finalResult;
}

export async function topMatchesFromCv(formData) {
  const primaryPayload = cloneFormData(formData);
  const primaryResponse = await fetch(
    `${API_BASE}/api/jobs/top-matches/general-from-cv`,
    {
      method: "POST",
      body: primaryPayload,
    },
  );

  if (primaryResponse.ok) {
    return primaryResponse.json();
  }

  // Backward compatibility: some running servers may not include the new route yet.
  if (primaryResponse.status === 404) {
    const fallbackPayload = cloneFormData(formData);
    if (!fallbackPayload.has("jobs")) {
      fallbackPayload.append("jobs", "[]");
    }

    const fallbackResponse = await fetch(
      `${API_BASE}/api/jobs/top-matches/from-cv`,
      {
        method: "POST",
        body: fallbackPayload,
      },
    );

    if (fallbackResponse.ok) {
      return fallbackResponse.json();
    }
  }

  throw new Error("Failed to fetch top job matches.");
}

export async function fullCvAnalysisFromCv(formData) {
  const response = await fetch(`${API_BASE}/api/cv/full-analysis`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    throw new Error("Failed to fetch full CV analysis report.");
  }

  return response.json();
}

export async function createPostedJob(payload) {
  const response = await fetch(`${API_BASE}/api/jobs/posted`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    throw new Error("Failed to create posted job.");
  }

  return response.json();
}

export async function seedRealisticJobs() {
  const response = await fetch(`${API_BASE}/api/jobs/posted/seed-realistic`, {
    method: "POST",
  });

  if (!response.ok) {
    throw new Error("Failed to seed realistic jobs.");
  }

  return response.json();
}

export async function listPostedJobs() {
  const response = await fetch(`${API_BASE}/api/jobs/posted`, {
    method: "GET",
  });

  if (!response.ok) {
    throw new Error("Failed to fetch posted jobs.");
  }

  return response.json();
}

export async function getPostedJobDetails(jobId) {
  const response = await fetch(`${API_BASE}/api/jobs/posted/${jobId}`, {
    method: "GET",
  });

  if (!response.ok) {
    throw new Error("Failed to fetch job details.");
  }

  return response.json();
}

export async function applyToPostedJob(jobId, formData) {
  const payload = new FormData();
  const file = formData.get("file");
  if (!file) {
    throw new Error("CV file is missing.");
  }

  payload.append("job_id", jobId);
  payload.append("file", file);

  const response = await fetch(`${API_BASE}/api/jobs/apply`, {
    method: "POST",
    body: payload,
  });

  if (response.ok) {
    const data = await response.json();
    return {
      ...data,
      id: data.application_id || data.id || "",
      match_score:
        typeof data.match_score === "number"
          ? data.match_score
          : Number(data.score || 0),
    };
  }

  // Fallback to legacy endpoint to avoid blocking submissions in mixed deployments.
  const legacyPayload = new FormData();
  legacyPayload.append("file", file);
  legacyPayload.append(
    "candidate_name",
    formData.get("candidate_name") || "Candidate",
  );
  legacyPayload.append(
    "candidate_headline",
    formData.get("candidate_headline") || "AI Parsed Candidate",
  );
  legacyPayload.append(
    "candidate_skills",
    formData.get("candidate_skills") || "[]",
  );
  legacyPayload.append(
    "candidate_summary",
    formData.get("candidate_summary") || "",
  );

  const legacyResponse = await fetch(
    `${API_BASE}/api/jobs/posted/${jobId}/apply`,
    {
      method: "POST",
      body: legacyPayload,
    },
  );

  if (!legacyResponse.ok) {
    let detail = "Failed to apply for this job.";
    try {
      const errorData = await legacyResponse.json();
      detail = errorData.detail || detail;
    } catch {
      try {
        detail = await legacyResponse.text();
      } catch {
        // Ignore parse fallback errors.
      }
    }
    throw new Error(detail || "Failed to apply for this job.");
  }

  const legacyData = await legacyResponse.json();
  return {
    ...legacyData,
    id: legacyData.id || "",
    match_score: Number(legacyData.match_score || 0),
  };
}

export async function updatePostedJob(jobId, payload) {
  const response = await fetch(`${API_BASE}/api/jobs/posted/${jobId}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    throw new Error("Failed to update posted job.");
  }

  return response.json();
}

export async function deletePostedJob(jobId) {
  const response = await fetch(`${API_BASE}/api/jobs/posted/${jobId}`, {
    method: "DELETE",
  });

  if (!response.ok) {
    throw new Error("Failed to delete posted job.");
  }

  return response.json();
}

export async function getCompanyDashboard(filters = {}) {
  const params = new URLSearchParams();
  if (filters.sort_by) params.set("sort_by", filters.sort_by);
  if (filters.order) params.set("order", filters.order);
  if (
    filters.min_score !== "" &&
    filters.min_score !== undefined &&
    filters.min_score !== null
  ) {
    params.set("min_score", String(filters.min_score));
  }
  if (filters.since_date) params.set("since_date", filters.since_date);

  const query = params.toString();
  const response = await fetch(
    `${API_BASE}/api/jobs/company/dashboard${query ? `?${query}` : ""}`,
    {
      method: "GET",
    },
  );

  if (!response.ok) {
    throw new Error("Failed to fetch company dashboard.");
  }

  return response.json();
}

export async function chatInterview(sessionId, message) {
  const response = await fetch(`${API_BASE}/api/chat/interview`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId, message }),
  });

  if (!response.ok) {
    throw new Error("Failed to run interview chat.");
  }

  return response.json();
}

export async function startInterview(applicationId) {
  const response = await fetch(`${API_BASE}/api/chat/interview/start`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ application_id: applicationId }),
  });

  if (!response.ok) {
    throw new Error("Failed to start interview.");
  }

  return response.json();
}

export async function answerInterview(sessionId, answer) {
  const response = await fetch(`${API_BASE}/api/chat/interview/answer`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId, answer }),
  });

  if (!response.ok) {
    throw new Error("Failed to submit interview answer.");
  }

  return response.json();
}

export async function getInterviewReport(sessionId) {
  const response = await fetch(
    `${API_BASE}/api/chat/interview/report/${sessionId}`,
    {
      method: "GET",
    },
  );

  if (!response.ok) {
    throw new Error("Failed to fetch interview report.");
  }

  return response.json();
}

export async function registerAccount(payload) {
  const response = await fetch(`${API_BASE}/api/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    if (response.status === 404) {
      throw new Error(
        "Auth API is not available on the current backend. Restart the backend with backend.app.main:app.",
      );
    }
    const rawBody = await response.text().catch(() => "");
    let detail = "";
    try {
      detail = JSON.parse(rawBody).detail || "";
    } catch {
      detail = rawBody;
    }
    throw new Error(detail || "Failed to register account.");
  }

  return response.json();
}

export async function loginAccount(payload) {
  const response = await fetch(`${API_BASE}/api/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    if (response.status === 404) {
      throw new Error(
        "Auth API is not available on the current backend. Restart the backend with backend.app.main:app.",
      );
    }
    const rawBody = await response.text().catch(() => "");
    let detail = "";
    try {
      detail = JSON.parse(rawBody).detail || "";
    } catch {
      detail = rawBody;
    }
    throw new Error(detail || "Failed to login.");
  }

  return response.json();
}

export async function getCurrentAccount(accessToken) {
  const response = await fetch(`${API_BASE}/api/auth/me`, {
    method: "GET",
    headers: {
      Authorization: `Bearer ${accessToken}`,
      "X-Session-Token": accessToken,
    },
  });

  if (!response.ok) {
    throw new Error("Failed to fetch current account.");
  }

  return response.json();
}

export async function logoutAccount(accessToken) {
  const response = await fetch(`${API_BASE}/api/auth/logout`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${accessToken}`,
      "X-Session-Token": accessToken,
    },
  });

  if (!response.ok) {
    throw new Error("Failed to logout.");
  }

  return response.json();
}

export async function getLatestInterview(applicationId) {
  const response = await fetch(
    `${API_BASE}/api/chat/interview/latest/${applicationId}`,
    {
      method: "GET",
    },
  );

  if (!response.ok) {
    throw new Error("Failed to fetch latest interview.");
  }

  return response.json();
}

export async function preMatchCv(jobId, formData) {
  const payload = cloneFormData(formData);
  if (!payload.has("job_id")) {
    payload.append("job_id", jobId);
  }

  const response = await fetch(`${API_BASE}/api/jobs/pre-match`, {
    method: "POST",
    body: payload,
  });

  if (!response.ok) {
    throw new Error("Failed to pre-match CV.");
  }

  return response.json();
}

export async function submitRecruiterFeedback(payload) {
  const response = await fetch(`${API_BASE}/api/feedback`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    throw new Error("Failed to submit feedback.");
  }

  return response.json();
}

export async function getRecruiterFeedback(applicationId) {
  const response = await fetch(`${API_BASE}/api/feedback/${applicationId}`, {
    method: "GET",
  });

  if (!response.ok) {
    if (response.status === 404) return null;
    throw new Error("Failed to fetch feedback.");
  }

  return response.json();
}

export async function getFeedbackAnalytics() {
  const response = await fetch(`${API_BASE}/api/feedback/analytics`, {
    method: "GET",
  });

  if (!response.ok) {
    throw new Error("Failed to fetch feedback analytics.");
  }

  return response.json();
}

export async function trainLtrModel() {
  const response = await fetch(`${API_BASE}/api/feedback/ltr/train`, {
    method: "POST",
  });

  if (!response.ok) {
    throw new Error("Failed to train LTR model.");
  }

  return response.json();
}

export async function getLtrInfo() {
  const response = await fetch(`${API_BASE}/api/feedback/ltr/info`, {
    method: "GET",
  });

  if (!response.ok) {
    throw new Error("Failed to fetch LTR info.");
  }

  return response.json();
}

