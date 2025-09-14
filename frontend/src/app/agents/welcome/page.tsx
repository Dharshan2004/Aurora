import ChatStream from "@/components/ChatStream";

export const metadata = {
  title: "Aurora — Welcome Agent",
  description:
    "Onboarding FAQ agent that streams responses from the backend.",
};

export default function WelcomeAgentPage() {
  return (
    <main className="min-h-screen bg-neutral-950 text-neutral-100">
      <div className="mx-auto max-w-5xl px-4 py-8">
        <div className="mb-6">
          <h1 className="text-3xl font-bold">Aurora — Welcome Agent 👋</h1>
          <p className="text-neutral-400 mt-2">
            Ask onboarding questions from policy docs and handbooks. Get instant answers with citations.
          </p>
          <div className="mt-4 p-4 rounded-xl bg-blue-900/20 border border-blue-800">
            <h3 className="font-semibold text-blue-300 mb-2">💡 Try asking:</h3>
            <ul className="text-sm text-blue-200 space-y-1">
              <li>• &quot;How do I submit a leave request?&quot;</li>
              <li>• &quot;What&apos;s the travel expense policy?&quot;</li>
              <li>• &quot;Who do I contact for IT support?&quot;</li>
              <li>• &quot;What are the working hours?&quot;</li>
            </ul>
          </div>
        </div>
        <ChatStream />
      </div>
    </main>
  );
}
