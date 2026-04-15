import { Link } from "react-router-dom";

export default function RoleSelectionPage() {
  return (
    <main
      className="mx-auto flex min-h-screen w-full max-w-6xl items-center px-4 py-8 sm:px-6"
      dir="ltr"
    >
      <section className="grid w-full gap-5 lg:grid-cols-[1.2fr_0.8fr]">
        <article className="glass rounded-3xl border border-white/80 p-6 shadow-panel md:p-10">
          <p className="text-xs font-bold uppercase tracking-[0.16em] text-brand-600">
            HireMind Platform
          </p>
          <h1 className="mt-3 text-4xl font-black leading-tight text-slate-900 md:text-5xl">
            Build your hiring story with AI precision
          </h1>
          <p className="mt-4 max-w-xl text-base text-slate-600">
            Choose a dedicated workspace for talent or hiring teams. Clean
            workflows, smart scoring, and interview intelligence in one SaaS
            experience.
          </p>

          <div className="mt-8 grid gap-3 sm:grid-cols-3">
            {["Semantic matching", "AI interviews", "Hiring analytics"].map(
              (item) => (
                <div
                  key={item}
                  className="rounded-2xl border border-brand-100 bg-white px-4 py-3 text-sm font-semibold text-slate-700"
                >
                  {item}
                </div>
              ),
            )}
          </div>
        </article>

        <section className="grid gap-4">
          <article className="glass rounded-3xl border border-white/80 p-6 shadow-soft">
            <h2 className="text-xl font-bold text-slate-900">Company Portal</h2>
            <p className="mt-2 text-sm text-slate-600">
              Post jobs, track applicants, and rank candidates with AI signals.
            </p>
            <Link
              to="/auth?role=company"
              className="mt-5 inline-flex rounded-xl bg-brand-500 px-4 py-2.5 text-sm font-bold text-white transition hover:bg-brand-600"
            >
              Sign in as Company
            </Link>
          </article>

          <article className="glass rounded-3xl border border-white/80 p-6 shadow-soft">
            <h2 className="text-xl font-bold text-slate-900">
              Candidate Portal
            </h2>
            <p className="mt-2 text-sm text-slate-600">
              Analyze your CV, discover matching jobs, and take adaptive AI
              interviews.
            </p>
            <Link
              to="/auth?role=candidate"
              className="mt-5 inline-flex rounded-xl bg-slate-900 px-4 py-2.5 text-sm font-bold text-white transition hover:bg-slate-700"
            >
              Sign in as Candidate
            </Link>
          </article>
        </section>
      </section>
    </main>
  );
}
