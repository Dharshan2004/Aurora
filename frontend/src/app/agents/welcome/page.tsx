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
          <h1 className="text-3xl font-bold">Aurora — Welcome Agent</h1>
          <p className="text-neutral-400">
            Ask onboarding questions from policy docs and handbooks.
          </p>
        </div>
        <ChatStream />
      </div>
    </main>
  );
}
