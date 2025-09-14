import ChatStream from "@/components/ChatStream";

export const metadata = {
  title: "Aurora — Skill Navigator",
  description:
    "AI-powered skill development planning with personalized 30-60 day learning paths.",
};

export default function SkillNavPage() {
  return (
    <main className="min-h-screen bg-neutral-950 text-neutral-100">
      <div className="mx-auto max-w-5xl px-4 py-8">
        <div className="mb-6">
          <h1 className="text-3xl font-bold">Aurora — Skill Navigator 🧭</h1>
          <p className="text-neutral-400 mt-2">
            Get personalized 30–60 day learning plans aligned to your skills gaps and career goals.
          </p>
          <div className="mt-4 p-4 rounded-xl bg-blue-900/20 border border-blue-800">
            <h3 className="font-semibold text-blue-300 mb-2">💡 Try asking:</h3>
            <ul className="text-sm text-blue-200 space-y-1">
              <li>• &quot;Create a learning plan for a backend developer role&quot;</li>
              <li>• &quot;I need to improve my Python and cloud skills&quot;</li>
              <li>• &quot;Plan my growth from junior to senior developer&quot;</li>
              <li>• &quot;What should I learn for data science?&quot;</li>
            </ul>
          </div>
        </div>
        <ChatStream 
          endpoint="/api/aurora/agents/skillnav/stream"
          title="Skill Navigator"
          placeholder="Describe your role, current skills, and learning goals..."
        />
      </div>
    </main>
  );
}
