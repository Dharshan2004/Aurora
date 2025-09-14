import Link from "next/link";

export default function Home() {
  return (
    <main className="relative aurora-bg">
      <section className="mx-auto max-w-6xl px-6 pt-24 pb-16">
        <div className="mx-auto max-w-3xl text-center space-y-6">
          <h1 className="text-5xl font-bold tracking-tight">Aurora</h1>
          <p className="text-lg text-neutral-300">
            Aurora is an AI ecosystem that empowers young professionals from onboarding to leadership
            by providing personalized guidance, skills growth planning, and transparent feedback.
          </p>
          <p className="text-neutral-300">
            Our mission: align with SAP’s motto ‘help the world run better and improve people’s lives’
            while showcasing Responsible AI and business scalability.
          </p>

          <div className="flex items-center justify-center gap-3 pt-2 flex-wrap">
            <Link
              href="/agents/welcome"
              className="rounded-xl bg-blue-600 px-5 py-3 font-medium text-white hover:bg-blue-500 transition"
            >
              🚀 Start with Welcome Agent
            </Link>
            <Link
              href="/agents/skillnav"
              className="rounded-xl bg-purple-600 px-5 py-3 font-medium text-white hover:bg-purple-500 transition"
            >
              🧭 Skill Navigator
            </Link>
            <Link
              href="/agents/progress"
              className="rounded-xl bg-green-600 px-5 py-3 font-medium text-white hover:bg-green-500 transition"
            >
              📈 Progress Tracker
            </Link>
          </div>
        </div>

        {/* Feature cards */}
        <div className="mt-16 grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
          <div className="rounded-2xl border border-neutral-800 bg-neutral-900/40 p-5 hover:border-neutral-700 transition">
            <div className="text-2xl">👋</div>
            <h3 className="mt-3 font-semibold">Welcome Agent</h3>
            <p className="text-sm text-neutral-400">
              Answers onboarding FAQs from policy docs and handbooks.
            </p>
            <Link href="/agents/welcome" className="mt-4 inline-block text-sm text-blue-400 hover:text-blue-300">
              Open →
            </Link>
          </div>

          <div className="rounded-2xl border border-neutral-800 bg-neutral-900/40 p-5 hover:border-neutral-700 transition">
            <div className="text-2xl">🧭</div>
            <h3 className="mt-3 font-semibold">Skill Navigator</h3>
            <p className="text-sm text-neutral-400">
              Personalized 30–60 day learning plans aligned to skills gaps.
            </p>
            <Link href="/agents/skillnav" className="mt-4 inline-block text-sm text-purple-400 hover:text-purple-300">
              Try it now →
            </Link>
          </div>

          <div className="rounded-2xl border border-neutral-800 bg-neutral-900/40 p-5 hover:border-neutral-700 transition">
            <div className="text-2xl">📈</div>
            <h3 className="mt-3 font-semibold">Progress Companion</h3>
            <p className="text-sm text-neutral-400">
              Weekly growth summaries with transparent, auditable sources.
            </p>
            <Link href="/agents/progress" className="mt-4 inline-block text-sm text-green-400 hover:text-green-300">
              Try it now →
            </Link>
          </div>

          <div className="rounded-2xl border border-neutral-800 bg-neutral-900/40 p-5 hover:border-neutral-700 transition">
            <div className="text-2xl">🔍</div>
            <h3 className="mt-3 font-semibold">Audit Dashboard</h3>
            <p className="text-sm text-neutral-400">
              Transparent AI decision tracking with HMAC-verified logs.
            </p>
            <span className="mt-4 inline-block text-sm text-neutral-500">Coming soon</span>
          </div>
        </div>
      </section>
    </main>
  );
}
