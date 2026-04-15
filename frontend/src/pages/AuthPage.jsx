import { useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import {
  loginAccount,
  registerAccount,
  setStoredAuthSession,
} from "../api/client";

const ROLE_OPTIONS = [
  { value: "candidate", label: "Candidate" },
  { value: "company", label: "Company" },
];

const DEMO_ACCOUNTS = {
  company: {
    email: "company@hiremind.ai",
    password: "HireMind123!",
  },
  candidate: {
    email: "candidate@hiremind.ai",
    password: "HireMind123!",
  },
};

function getPortalPath(role) {
  return role === "company" ? "/company/dashboard" : "/candidate/dashboard";
}

export default function AuthPage({ onAuthSuccess, currentUser }) {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [mode, setMode] = useState("login");
  const [role, setRole] = useState(
    searchParams.get("role") || currentUser?.role || "candidate",
  );
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [form, setForm] = useState({
    full_name: "",
    company_name: "",
    email: DEMO_ACCOUNTS[role].email,
    password: DEMO_ACCOUNTS[role].password,
  });

  useEffect(() => {
    setForm((prev) => ({
      ...prev,
      email: DEMO_ACCOUNTS[role].email,
      password: DEMO_ACCOUNTS[role].password,
    }));
  }, [role]);

  async function handleSubmit(event) {
    event.preventDefault();
    setLoading(true);
    setError("");

    try {
      const response =
        mode === "register"
          ? await registerAccount({
              full_name: form.full_name,
              company_name: form.company_name,
              email: form.email,
              password: form.password,
              role,
            })
          : await loginAccount({ email: form.email, password: form.password });

      setStoredAuthSession(response);
      onAuthSuccess?.(response);
      navigate(getPortalPath(response.user?.role || role), { replace: true });
    } catch (submissionError) {
      setError(submissionError.message || "Unable to continue.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main
      className="mx-auto flex min-h-screen w-full max-w-6xl items-center px-4 py-8 sm:px-6"
      dir="ltr"
    >
      <section className="grid w-full gap-5 lg:grid-cols-2">
        <article className="glass hidden rounded-3xl border border-white/80 p-8 shadow-panel lg:block">
          <p className="text-xs font-bold uppercase tracking-[0.2em] text-brand-600">
            HireMind Access
          </p>
          <h1 className="mt-3 text-4xl font-black leading-tight text-slate-900">
            AI-driven hiring, designed for speed
          </h1>
          <p className="mt-4 max-w-md text-slate-600">
            One platform for CV intelligence, job matching, and interview
            evaluation. Sign in to access your workspace.
          </p>

          <div className="mt-8 grid gap-3">
            <div className="rounded-2xl border border-brand-100 bg-white p-4">
              <p className="text-sm font-bold text-slate-900">Candidates</p>
              <p className="mt-1 text-sm text-slate-600">
                CV analysis, job matching, AI interview scores.
              </p>
            </div>
            <div className="rounded-2xl border border-brand-100 bg-white p-4">
              <p className="text-sm font-bold text-slate-900">Companies</p>
              <p className="mt-1 text-sm text-slate-600">
                Jobs, applicants pipeline, and ranked hiring decisions.
              </p>
            </div>
          </div>
        </article>

        <article className="glass rounded-3xl border border-white/80 p-5 shadow-soft sm:p-7">
          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              onClick={() => setMode("login")}
              className={`rounded-xl px-4 py-2 text-sm font-bold transition ${
                mode === "login"
                  ? "bg-brand-500 text-white"
                  : "bg-white text-slate-600 hover:text-brand-600"
              }`}
            >
              Login
            </button>
            <button
              type="button"
              onClick={() => setMode("register")}
              className={`rounded-xl px-4 py-2 text-sm font-bold transition ${
                mode === "register"
                  ? "bg-brand-500 text-white"
                  : "bg-white text-slate-600 hover:text-brand-600"
              }`}
            >
              Register
            </button>
          </div>

          <div className="mt-4 flex flex-wrap gap-2">
            {ROLE_OPTIONS.map((item) => (
              <button
                key={item.value}
                type="button"
                onClick={() => setRole(item.value)}
                className={`rounded-full px-4 py-1.5 text-sm font-semibold transition ${
                  role === item.value
                    ? "bg-slate-900 text-white"
                    : "bg-white text-slate-600"
                }`}
              >
                {item.label}
              </button>
            ))}
          </div>

          <form className="mt-5 space-y-3" onSubmit={handleSubmit}>
            {mode === "register" && (
              <label className="block">
                <span className="mb-1.5 block text-sm font-semibold text-slate-700">
                  Full name
                </span>
                <input
                  value={form.full_name}
                  onChange={(event) =>
                    setForm((prev) => ({
                      ...prev,
                      full_name: event.target.value,
                    }))
                  }
                  required
                  className="w-full rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-sm outline-none focus:border-brand-400 focus:ring-2 focus:ring-brand-100"
                />
              </label>
            )}

            {mode === "register" && role === "company" && (
              <label className="block">
                <span className="mb-1.5 block text-sm font-semibold text-slate-700">
                  Company name
                </span>
                <input
                  value={form.company_name}
                  onChange={(event) =>
                    setForm((prev) => ({
                      ...prev,
                      company_name: event.target.value,
                    }))
                  }
                  required
                  className="w-full rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-sm outline-none focus:border-brand-400 focus:ring-2 focus:ring-brand-100"
                />
              </label>
            )}

            <label className="block">
              <span className="mb-1.5 block text-sm font-semibold text-slate-700">
                Email
              </span>
              <input
                type="email"
                value={form.email}
                onChange={(event) =>
                  setForm((prev) => ({ ...prev, email: event.target.value }))
                }
                required
                className="w-full rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-sm outline-none focus:border-brand-400 focus:ring-2 focus:ring-brand-100"
              />
            </label>

            <label className="block">
              <span className="mb-1.5 block text-sm font-semibold text-slate-700">
                Password
              </span>
              <input
                type="password"
                value={form.password}
                onChange={(event) =>
                  setForm((prev) => ({ ...prev, password: event.target.value }))
                }
                minLength={8}
                required
                className="w-full rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-sm outline-none focus:border-brand-400 focus:ring-2 focus:ring-brand-100"
              />
            </label>

            {error ? (
              <p className="text-sm font-semibold text-rose-600">{error}</p>
            ) : null}

            <button
              type="submit"
              disabled={loading}
              className="w-full rounded-xl bg-brand-500 px-4 py-2.5 text-sm font-bold text-white transition hover:bg-brand-600 disabled:opacity-60"
            >
              {loading
                ? "Please wait..."
                : mode === "login"
                  ? "Login"
                  : "Create account"}
            </button>

            <button
              type="button"
              onClick={() =>
                setForm((prev) => ({
                  ...prev,
                  email: DEMO_ACCOUNTS[role].email,
                  password: DEMO_ACCOUNTS[role].password,
                }))
              }
              className="w-full rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-sm font-semibold text-slate-700 transition hover:border-brand-200 hover:text-brand-700"
            >
              Use demo {role} credentials
            </button>
          </form>
        </article>
      </section>
    </main>
  );
}
