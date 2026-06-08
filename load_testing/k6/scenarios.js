import http from "k6/http";
import { check, group, sleep } from "k6";
import { SharedArray } from "k6/data";

const BASE_URL = __ENV.BASE_URL || "http://localhost:8000";
const PERF_EMAIL = __ENV.PERF_TEST_EMAIL || "perf+recruiter@hiremind.test";
const PERF_PASSWORD = __ENV.PERF_TEST_PASSWORD || "PerfTest123!";
const RESUME_TEXT = new SharedArray("resume", function () {
  return [open("./sample_resume.txt", "b")];
})[0];

export let options = {
  thresholds: {
    http_req_duration: ["p(95)<2000", "p(99)<5000"],
    http_req_failed: ["rate<0.01"],
  },
};

function auth() {
  const loginPayload = JSON.stringify({
    email: PERF_EMAIL,
    password: PERF_PASSWORD,
  });
  const loginRes = http.post(`${BASE_URL}/api/auth/login`, loginPayload, {
    headers: { "Content-Type": "application/json" },
  });

  if (!check(loginRes, { "logged in successfully": (r) => r.status === 200 })) {
    return null;
  }

  return loginRes.json().session_token;
}

function registerAndLogin() {
  const payload = JSON.stringify({
    email: PERF_EMAIL,
    password: PERF_PASSWORD,
    full_name: "HireMind Performance Recruiter",
    role: "company",
    company_name: "HireMind Performance",
  });

  http.post(`${BASE_URL}/api/auth/register`, payload, {
    headers: { "Content-Type": "application/json" },
  });

  return auth();
}

function getToken() {
  let token = auth();
  if (!token) {
    token = registerAndLogin();
  }
  return token;
}

function createJob(token) {
  const jobPayload = JSON.stringify({
    title: "Performance Test Job - Backend Engineer",
    description:
      "Enterprise resume and matching workload for HireMind performance validation.",
    required_skills: ["python", "fastapi", "postgresql", "docker"],
    responsibilities: [
      "Build distributed services",
      "Implement workflow orchestration",
      "Support enterprise reliability",
    ],
    preferred_skills: ["rabbitmq", "cloud", "observability"],
    tools: ["git", "docker", "kubernetes"],
    experience_level: "Senior",
    domain: "backend",
    hiring_rules: {
      mandatory_skills: ["python", "sql"],
      preferred_skills: ["docker", "cloud"],
      min_experience_years: 5,
    },
  });
  const res = http.post(`${BASE_URL}/api/jobs/posted`, jobPayload, {
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
  });
  return res.json()?.id || null;
}

function uploadResume(token) {
  const formData = {
    file: http.file(RESUME_TEXT, "resume.txt", "text/plain"),
    job_title: "Backend Engineer",
    job_description: "Candidate resume upload test for enterprise traffic.",
    required_skills: JSON.stringify(["python", "sql", "fastapi"]),
  };
  const res = http.post(`${BASE_URL}/api/cv/analyze`, formData, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });
  check(res, { "resume analyzed": (r) => r.status === 200 });
  return res;
}

function topMatchesFromCv(token) {
  const formData = {
    file: http.file(RESUME_TEXT, "resume.txt", "text/plain"),
  };
  const res = http.post(
    `${BASE_URL}/api/jobs/top-matches/general-from-cv`,
    formData,
    {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    },
  );
  check(res, { "top matches computed": (r) => r.status === 200 });
  return res;
}

function runSupervisorWorkflow(token, jobId) {
  const payload = JSON.stringify({
    job_id: jobId,
    cv_text:
      "Experienced backend engineer with deployment and performance experience.",
  });
  const res = http.post(`${BASE_URL}/api/agents/pipeline/run`, payload, {
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
  });
  check(res, { "supervisor workflow executed": (r) => r.status === 200 });
  return res;
}

export function setup() {
  const token = getToken();
  if (!token) {
    throw new Error("Failed to obtain performance test token.");
  }
  const jobId = createJob(token);
  if (!jobId) {
    throw new Error("Failed to create performance test job.");
  }
  return { token, jobId };
}

export default function (data) {
  const scenario = __ENV.PERF_SCENARIO || "candidate_upload";
  const token = data.token;
  const jobId = data.jobId;

  switch (scenario) {
    case "candidate_upload":
      group("Candidate Resume Upload", () => {
        uploadResume(token);
      });
      break;
    case "candidate_matching":
      group("Candidate Matching", () => {
        topMatchesFromCv(token);
      });
      break;
    case "recruiter_workflow":
      group("Recruiter Workflow", () => {
        uploadResume(token);
      });
      break;
    case "multi_agent_workflow":
      group("Multi-Agent Workflow", () => {
        runSupervisorWorkflow(token, jobId);
      });
      break;
    default:
      group("Candidate Resume Upload", () => {
        uploadResume(token);
      });
  }

  sleep(1);
}
