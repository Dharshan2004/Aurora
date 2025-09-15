"use client";

import { useEffect, useRef, useState } from "react";

type Props = {
  endpoint?: string; // default: /api/aurora/agents/welcome/stream
  title?: string;
  placeholder?: string;
};

export default function ChatStream({
  endpoint = "/api/aurora/agents/welcome/stream",
  title = "Welcome Agent",
  placeholder = "Ask an onboarding question…",
}: Props) {
  const [input, setInput] = useState("");
  const [streaming, setStreaming] = useState(false);
  const [output, setOutput] = useState<string>("");
  const [error, setError] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);
  const preRef = useRef<HTMLPreElement | null>(null);

  useEffect(() => {
    if (preRef.current) preRef.current.scrollTop = preRef.current.scrollHeight;
  }, [output]);

  async function send() {
    const msg = input.trim();
    if (!msg || streaming) return;
    setError(null);
    setOutput(""); // reset for each request
    setStreaming(true);

    console.log(`🌐 Frontend: Sending request to ${endpoint}`);
    console.log(`🌐 Frontend: Message: "${msg}"`);

    const controller = new AbortController();
    abortRef.current = controller;

    try {
      const res = await fetch(endpoint, {
        method: "POST",
        credentials: "include",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ msg }),
        signal: controller.signal,
      });

      console.log(`🌐 Frontend: Response status: ${res.status}`);
      console.log(`🌐 Frontend: Response headers:`, Object.fromEntries(res.headers.entries()));

      if (!res.ok || !res.body) {
        const text = await res.text().catch(() => "");
        console.log(`🌐 Frontend: Error response: ${text}`);
        throw new Error(text || `Request failed: ${res.status} ${res.statusText}`);
      }

      const reader = res.body.getReader();
      const decoder = new TextDecoder();

      console.log("🌐 Frontend: Starting to read stream");
      let totalChunks = 0;
      let totalContent = "";

      while (true) {
        const { value, done } = await reader.read();
        if (done) {
          console.log(`🌐 Frontend: Stream complete. Total chunks: ${totalChunks}, Total content length: ${totalContent.length}`);
          console.log(`🌐 Frontend: Final content preview: ${totalContent.substring(0, 200)}...`);
          break;
        }
        const chunk = decoder.decode(value, { stream: true });
        totalChunks++;
        totalContent += chunk;
        console.log(`🌐 Frontend: Chunk ${totalChunks}: "${chunk}"`);
        setOutput((prev) => {
          const newOutput = prev + chunk;
          console.log(`🌐 Frontend: Updated output length: ${newOutput.length}`);
          return newOutput;
        });
      }
    } catch (e: unknown) {
      console.log(`🌐 Frontend: Error occurred:`, e);
      if (e instanceof Error && e.name !== "AbortError") {
        console.log(`🌐 Frontend: Setting error: ${e.message}`);
        setError(e.message ?? "Something went wrong");
      }
    } finally {
      console.log(`🌐 Frontend: Request completed. Streaming: ${streaming}`);
      setStreaming(false);
      abortRef.current = null;
    }
  }

  function stop() {
    abortRef.current?.abort();
    abortRef.current = null;
    setStreaming(false);
  }

  return (
    <div className="mx-auto max-w-3xl p-4 space-y-4">
      <div className="rounded-2xl border border-neutral-800 bg-neutral-900/60 p-4">
        <h1 className="text-xl font-semibold text-white">{title}</h1>
        <p className="text-sm text-neutral-400">
          Ask onboarding questions. The response streams token-by-token from the backend.
        </p>
      </div>

      <div className="rounded-2xl border border-neutral-800 bg-neutral-900/40 p-4 space-y-3">
        <label className="block text-sm text-neutral-300">Your question</label>
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder={placeholder}
          rows={3}
          className="w-full rounded-xl border border-neutral-700 bg-neutral-900 px-3 py-2 text-white outline-none focus:ring-2 focus:ring-blue-500"
        />
        <div className="flex items-center gap-3">
          <button
            onClick={send}
            disabled={streaming || input.trim().length === 0}
            className="rounded-xl bg-blue-600 px-4 py-2 text-white disabled:opacity-50 disabled:cursor-not-allowed hover:bg-blue-500 transition"
          >
            {streaming ? "Streaming…" : "Send"}
          </button>
          <button
            onClick={stop}
            disabled={!streaming}
            className="rounded-xl bg-neutral-700 px-4 py-2 text-white disabled:opacity-50 disabled:cursor-not-allowed hover:bg-neutral-600 transition"
          >
            Stop
          </button>
        </div>
      </div>

      <div className="rounded-2xl border border-neutral-800 bg-neutral-950 p-4">
        <label className="block text-sm text-neutral-300 mb-2">Agent response</label>
        <pre
          ref={preRef}
          className="h-72 w-full overflow-auto whitespace-pre-wrap rounded-xl bg-neutral-900 p-3 text-neutral-100"
        >
{output || (!streaming && !error ? "" : "")}
        </pre>
        {error && <div className="mt-2 text-sm text-red-400">{error}</div>}
      </div>
    </div>
  );
}
