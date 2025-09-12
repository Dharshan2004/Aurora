import ChatStream from "@/components/ChatStream";

export const metadata = {
  title: "Aurora — Progress Companion",
  description:
    "Track learning progress and get motivational nudges for continuous growth.",
};

export default function ProgressPage() {
  return (
    <main className="min-h-screen bg-neutral-950 text-neutral-100">
      <div className="mx-auto max-w-5xl px-4 py-8">
        <div className="mb-6">
          <h1 className="text-3xl font-bold">Aurora — Progress Companion 📈</h1>
          <p className="text-neutral-400 mt-2">
            Weekly growth summaries with transparent, auditable sources and motivational nudges.
          </p>
          <div className="mt-4 p-4 rounded-xl bg-green-900/20 border border-green-800">
            <h3 className="font-semibold text-green-300 mb-2">💡 Try asking:</h3>
            <ul className="text-sm text-green-200 space-y-1">
              <li>• "Show my learning progress this month"</li>
              <li>• "What courses should I complete next?"</li>
              <li>• "Give me a motivation boost"</li>
              <li>• "How am I doing compared to my goals?"</li>
            </ul>
          </div>
        </div>
        <ChatStream 
          endpoint="/api/aurora/agents/progress/stream"
          title="Progress Companion"
          placeholder="Ask about your learning progress, goals, or need motivation..."
        />
      </div>
    </main>
  );
}
