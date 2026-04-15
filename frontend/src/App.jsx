import { useEffect, useMemo, useState } from "react";
import { Navigate, Route, Routes } from "react-router-dom";
import {
  applyToPostedJob,
  clearStoredAuthSession,
  createPostedJob,
  deletePostedJob,
  getCompanyDashboard,
  getCurrentAccount,
  getStoredAuthSession,
  listPostedJobs,
  logoutAccount,
  seedRealisticJobs,
  setStoredAuthSession,
  updatePostedJob,
} from "./api/client";
import { Toast } from "./components/SaaSPrimitives";
import AppLayout from "./layout/AppLayout";
import ApplicantsPage from "./pages/ApplicantsPage";
import AuthPage from "./pages/AuthPage";
import CandidateAnalysisPage from "./pages/CandidateAnalysisPage";
import CandidateDashboardPage from "./pages/CandidateDashboardPage";
import CandidateInterviewPage from "./pages/CandidateInterviewPage";
import CandidateJobsPage from "./pages/CandidateJobsPage";
import CandidateMatchingPage from "./pages/CandidateMatchingPage";
import CompanyAddJobPage from "./pages/CompanyAddJobPage";
import DashboardPage from "./pages/DashboardPage";
import JobsPage from "./pages/JobsPage";
import ReportsPage from "./pages/ReportsPage";
import RoleSelectionPage from "./pages/RoleSelectionPage";
import SettingsPage from "./pages/SettingsPage";
import ApplicationsPage from "./pages/ApplicationsPage";

const COMPANY_NAV = [
  { to: "/company/dashboard", label: "Dashboard" },
  { to: "/company/add-job", label: "Add Job" },
  { to: "/company/jobs", label: "Jobs List" },
  { to: "/company/applicants", label: "Applicants" },
  { to: "/company/ranking", label: "Candidate Ranking" },
  { to: "/company/settings", label: "Settings" },
];

const CANDIDATE_NAV = [
  { to: "/candidate/dashboard", label: "Dashboard" },
  { to: "/candidate/analysis", label: "CV Analysis" },
  { to: "/candidate/jobs", label: "Jobs" },
  { to: "/candidate/matching", label: "Job Matching" },
  { to: "/candidate/interview", label: "AI Interview" },
  { to: "/candidate/applications", label: "Applications" },
  { to: "/candidate/settings", label: "Settings" },
];

const COMPANY_TITLES = {
  "/company/dashboard": "Company Dashboard",
  "/company/add-job": "Add Job",
  "/company/jobs": "Jobs List",
  "/company/applicants": "Applicants",
  "/company/ranking": "Candidate Ranking",
  "/company/settings": "Settings",
};

const CANDIDATE_TITLES = {
  "/candidate/dashboard": "Candidate Dashboard",
  "/candidate/analysis": "CV Analysis",
  "/candidate/jobs": "Jobs",
  "/candidate/matching": "Job Matching",
  "/candidate/interview": "AI Interview",
  "/candidate/applications": "Applications",
  "/candidate/settings": "Settings",
};

function getPortalPath(role) {
  return role === "company" ? "/company/dashboard" : "/candidate/dashboard";
}

function PortalGuard({ allowedRole, currentUser, authReady, children }) {
  if (!authReady) {
    return (
      <main className="mx-auto flex min-h-screen w-full max-w-4xl items-center px-4">
        <div className="glass w-full rounded-3xl border border-white/80 p-8 text-center shadow-soft">
          <p className="text-sm font-semibold text-brand-600">HireMind</p>
          <h1 className="mt-2 text-3xl font-black text-slate-900">
            Loading workspace
          </h1>
          <p className="mt-2 text-slate-600">
            Checking your session and preparing your portal.
          </p>
        </div>
      </main>
    );
  }

  if (!currentUser) {
    return <Navigate to={`/auth?role=${allowedRole}`} replace />;
  }

  if (currentUser.role !== allowedRole) {
    return <Navigate to={getPortalPath(currentUser.role)} replace />;
  }

  return children;
}

export default function App() {
  const [jobs, setJobs] = useState([]);
  const [dashboard, setDashboard] = useState(null);
  const [latestApplicationId, setLatestApplicationId] = useState("");
  const [currentUser, setCurrentUser] = useState(null);
  const [authReady, setAuthReady] = useState(false);
  const [candidateApplications, setCandidateApplications] = useState([]);
  const [latestMatchResult, setLatestMatchResult] = useState(null);
  const [toast, setToast] = useState({ type: "success", message: "" });

  async function refreshData() {
    const [jobsResponse, dashboardResponse] = await Promise.all([
      listPostedJobs(),
      getCompanyDashboard(),
    ]);
    setJobs(jobsResponse.jobs || []);
    setDashboard(dashboardResponse || null);
  }

  useEffect(() => {
    const storedSession = getStoredAuthSession();

    if (!storedSession?.access_token) {
      setAuthReady(true);
      refreshData().catch(() => {
        setJobs([]);
        setDashboard(null);
      });
      return;
    }

    getCurrentAccount(storedSession.access_token)
      .then((account) => {
        setCurrentUser(account);
        setStoredAuthSession({ ...storedSession, user: account });
      })
      .catch(() => {
        clearStoredAuthSession();
        setCurrentUser(null);
      })
      .finally(() => {
        setAuthReady(true);
      });

    refreshData().catch(() => {
      setJobs([]);
      setDashboard(null);
    });
  }, []);

  useEffect(() => {
    if (!toast.message) return;
    const timer = setTimeout(
      () => setToast({ type: "success", message: "" }),
      3500,
    );
    return () => clearTimeout(timer);
  }, [toast]);

  const rankedCandidates = useMemo(() => {
    if (!dashboard?.jobs) return [];
    const rows = [];
    for (const jobItem of dashboard.jobs) {
      for (const applicant of jobItem.applicants || []) {
        rows.push({
          ...applicant,
          job_title: jobItem.job.title,
          final_score:
            Number(applicant.match_score || 0) * 0.65 +
            Number(applicant.interview_score || 0) * 0.35,
        });
      }
    }
    return rows.sort((a, b) => b.final_score - a.final_score);
  }, [dashboard]);

  async function handleAuthSuccess(session) {
    if (session?.user) {
      setCurrentUser(session.user);
      setStoredAuthSession(session);
    }
    await refreshData();
    setToast({ type: "success", message: "Welcome to HireMind." });
  }

  async function handleLogout() {
    const storedSession = getStoredAuthSession();
    try {
      if (storedSession?.access_token) {
        await logoutAccount(storedSession.access_token);
      }
    } catch {
      // Ignore logout API errors and clear local auth state anyway.
    }
    clearStoredAuthSession();
    setCurrentUser(null);
    setToast({ type: "success", message: "You have been logged out." });
  }

  async function handleCreateJob(payload) {
    await createPostedJob(payload);
    await refreshData();
    setToast({ type: "success", message: "Job created successfully." });
  }

  async function handleUpdateJob(jobId, payload) {
    await updatePostedJob(jobId, payload);
    await refreshData();
    setToast({ type: "success", message: "Job updated successfully." });
  }

  async function handleDeleteJob(jobId) {
    await deletePostedJob(jobId);
    await refreshData();
    setToast({ type: "success", message: "Job deleted." });
  }

  async function handleSeedRealisticJobs() {
    const response = await seedRealisticJobs();
    await refreshData();
    setToast({
      type: "success",
      message: `Seeded ${response.created_count || 0} jobs and updated ${response.updated_count || 0}.`,
    });
    return response;
  }

  async function handleCandidateApply(jobId, payload) {
    const response = await applyToPostedJob(jobId, payload);
    const appliedJob = jobs.find((job) => job.id === jobId);
    const record = {
      id: response.id || `local-${Date.now()}`,
      job_id: jobId,
      job_title: appliedJob?.title || "Selected Role",
      status: "pending",
      match_score: Number(response.match_score || 0),
      ai_score: 0,
      matched_skills:
        response.matched_keywords || response.matched_skills || [],
      missing_skills:
        response.missing_keywords || response.missing_skills || [],
      recommendation:
        response.feedback || "Profile is being reviewed by the hiring team.",
      created_at: new Date().toISOString(),
    };

    setCandidateApplications((prev) => [record, ...prev]);
    setLatestMatchResult(record);
    setLatestApplicationId(record.id);
    await refreshData();
    setToast({
      type: "success",
      message: "Application submitted successfully.",
    });
    return response;
  }

  return (
    <>
      <Routes>
        <Route
          path="/"
          element={
            currentUser ? (
              <Navigate to={getPortalPath(currentUser.role)} replace />
            ) : (
              <RoleSelectionPage />
            )
          }
        />

        <Route
          path="/auth"
          element={
            <AuthPage
              onAuthSuccess={handleAuthSuccess}
              currentUser={currentUser}
            />
          }
        />

        <Route
          element={
            <PortalGuard
              allowedRole="company"
              currentUser={currentUser}
              authReady={authReady}
            >
              <AppLayout
                navItems={COMPANY_NAV}
                titles={COMPANY_TITLES}
                portalTitle="HireMind Employers"
                portalSubtitle="Hiring Control Center"
                brandVariant="company"
                portalLabel="Company Portal"
                searchPlaceholder="Search jobs, applicants, reports"
                portalTheme="theme-company"
                currentUser={currentUser}
                onLogout={handleLogout}
              />
            </PortalGuard>
          }
        >
          <Route
            path="/company"
            element={<Navigate to="/company/dashboard" replace />}
          />
          <Route
            path="/company/dashboard"
            element={<DashboardPage dashboard={dashboard} />}
          />
          <Route
            path="/company/add-job"
            element={<CompanyAddJobPage onCreateJob={handleCreateJob} />}
          />
          <Route
            path="/company/jobs"
            element={
              <JobsPage
                jobs={jobs}
                onUpdateJob={handleUpdateJob}
                onDeleteJob={handleDeleteJob}
                onSeedJobs={handleSeedRealisticJobs}
              />
            }
          />
          <Route
            path="/company/applicants"
            element={
              <ApplicantsPage
                jobs={jobs}
                dashboard={dashboard}
                onDataChanged={refreshData}
              />
            }
          />
          <Route
            path="/company/ranking"
            element={<ReportsPage rankedCandidates={rankedCandidates} />}
          />
          <Route path="/company/settings" element={<SettingsPage />} />
        </Route>

        <Route
          element={
            <PortalGuard
              allowedRole="candidate"
              currentUser={currentUser}
              authReady={authReady}
            >
              <AppLayout
                navItems={CANDIDATE_NAV}
                titles={CANDIDATE_TITLES}
                portalTitle="HireMind Talent"
                portalSubtitle="Career Journey"
                brandVariant="candidate"
                portalLabel="Candidate Portal"
                searchPlaceholder="Search open roles and requirements"
                portalTheme="theme-candidate"
                currentUser={currentUser}
                onLogout={handleLogout}
              />
            </PortalGuard>
          }
        >
          <Route
            path="/candidate"
            element={<Navigate to="/candidate/dashboard" replace />}
          />
          <Route
            path="/candidate/dashboard"
            element={
              <CandidateDashboardPage
                jobs={jobs}
                latestApplicationId={latestApplicationId}
                latestMatchResult={latestMatchResult}
              />
            }
          />
          <Route
            path="/candidate/analysis"
            element={<CandidateAnalysisPage />}
          />
          <Route
            path="/candidate/jobs"
            element={
              <CandidateJobsPage jobs={jobs} onApply={handleCandidateApply} />
            }
          />
          <Route
            path="/candidate/matching"
            element={
              <CandidateMatchingPage latestMatchResult={latestMatchResult} />
            }
          />
          <Route
            path="/candidate/interview"
            element={
              <CandidateInterviewPage
                latestApplicationId={latestApplicationId}
              />
            }
          />
          <Route
            path="/candidate/applications"
            element={<ApplicationsPage applications={candidateApplications} />}
          />
          <Route path="/candidate/settings" element={<SettingsPage />} />
        </Route>

        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>

      <Toast
        type={toast.type}
        message={toast.message}
        onClose={() => setToast({ type: "success", message: "" })}
      />
    </>
  );
}
