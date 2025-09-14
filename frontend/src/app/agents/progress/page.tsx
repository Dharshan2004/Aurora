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
            Track your learning journey with intelligent progress analysis and personalized motivation.
          </p>
          
          {/* How It Works Section */}
          <div className="mt-6 p-6 rounded-xl bg-green-900/20 border border-green-800">
            <h3 className="font-semibold text-green-300 mb-3">🔍 How Progress Companion Works</h3>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 text-sm">
              <div className="space-y-2">
                <div className="font-medium text-green-200">1. Question Analysis</div>
                <p className="text-green-100">Understands what you're asking about (completed, pending, overdue, next steps)</p>
              </div>
              <div className="space-y-2">
                <div className="font-medium text-green-200">2. Data Processing</div>
                <p className="text-green-100">Analyzes your course completion data and due dates</p>
              </div>
              <div className="space-y-2">
                <div className="font-medium text-green-200">3. Smart Insights</div>
                <p className="text-green-100">Generates context-aware responses with progress percentages</p>
              </div>
              <div className="space-y-2">
                <div className="font-medium text-green-200">4. Motivation</div>
                <p className="text-green-100">Provides personalized nudges and encouragement</p>
              </div>
            </div>
          </div>

          {/* Question Types */}
          <div className="mt-4 p-4 rounded-xl bg-blue-900/20 border border-blue-800">
            <h3 className="font-semibold text-blue-300 mb-2">💬 Types of Questions You Can Ask</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
              <div className="space-y-3">
                <div className="space-y-1">
                  <div className="font-medium text-blue-200">📊 Progress Overview:</div>
                  <ul className="text-blue-100 space-y-1">
                    <li>• "Show my learning progress"</li>
                    <li>• "How am I doing this month?"</li>
                    <li>• "Give me a progress summary"</li>
                  </ul>
                </div>
                <div className="space-y-1">
                  <div className="font-medium text-blue-200">✅ Completed Work:</div>
                  <ul className="text-blue-100 space-y-1">
                    <li>• "What have I completed?"</li>
                    <li>• "Show me my achievements"</li>
                    <li>• "What courses did I finish?"</li>
                  </ul>
                </div>
              </div>
              <div className="space-y-3">
                <div className="space-y-1">
                  <div className="font-medium text-blue-200">⏳ Next Actions:</div>
                  <ul className="text-blue-100 space-y-1">
                    <li>• "What should I do next?"</li>
                    <li>• "What's my priority?"</li>
                    <li>• "What courses are pending?"</li>
                  </ul>
                </div>
                <div className="space-y-1">
                  <div className="font-medium text-blue-200">🚨 Urgent Items:</div>
                  <ul className="text-blue-100 space-y-1">
                    <li>• "What's overdue?"</li>
                    <li>• "What needs immediate attention?"</li>
                    <li>• "Show me urgent deadlines"</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>

          {/* Features */}
          <div className="mt-4 p-4 rounded-xl bg-neutral-800/50 border border-neutral-700">
            <h3 className="font-semibold text-neutral-300 mb-2">🎯 Key Features</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
              <div className="space-y-2">
                <div className="font-medium text-neutral-200">📈 Progress Tracking</div>
                <p className="text-neutral-400">Real-time completion percentages and milestone tracking</p>
              </div>
              <div className="space-y-2">
                <div className="font-medium text-neutral-200">⏰ Deadline Management</div>
                <p className="text-neutral-400">Identifies overdue courses and upcoming deadlines</p>
              </div>
              <div className="space-y-2">
                <div className="font-medium text-neutral-200">💪 Motivational Support</div>
                <p className="text-neutral-400">Personalized encouragement based on your progress level</p>
              </div>
            </div>
          </div>

          {/* Sample Data */}
          <div className="mt-4 p-4 rounded-xl bg-yellow-900/20 border border-yellow-800">
            <h3 className="font-semibold text-yellow-300 mb-2">📋 Sample Data Structure</h3>
            <div className="text-xs text-yellow-100 space-y-1">
              <div>• <span className="font-mono">user_id</span>: Unique identifier for personalized tracking</div>
              <div>• <span className="font-mono">course</span>: Course/module name</div>
              <div>• <span className="font-mono">status</span>: Completed, Assigned, In Progress</div>
              <div>• <span className="font-mono">due</span>: Deadline date (YYYY-MM-DD)</div>
              <div>• <span className="font-mono">attempts</span>: Number of quiz attempts</div>
            </div>
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
