# Aurora — Welcome Agent Frontend (Drop‑in for Next.js App Router)

This package contains a **minimal, secure frontend** for the *Welcome Agent* that streams responses from your FastAPI/LangGraph backend via a **Next.js Route Handler proxy**.

> Works best with a Next.js 14+ project created via `create-next-app` using **TypeScript**, **App Router**, and **Tailwind** (optional but recommended).

---

## What’s inside

- `src/app/agents/welcome/page.tsx` — Welcome Agent page with a streaming chat UI
- `src/components/ChatStream.tsx` — Streaming component (chunked fetch)
- `src/app/api/aurora/[...path]/route.ts` — Secure proxy to your FastAPI server (handles streaming)
- `src/lib/fetch.ts` — Lightweight typed JSON fetch helper
- `middleware.ts` — (Optional) Auth gate using JWT cookie
- `README.md` — This file

---

## Backend expectation

Your FastAPI/LangGraph backend should expose a **streaming endpoint** like:

```
POST /agents/welcome/stream
Body: { "msg": "..." }
Returns: chunked text or SSE stream
```

You can adjust the path in the frontend calls if your routes differ.

---

## How to integrate

1) **Copy files** into your Next.js project (preserving paths). For example, from the ZIP:

```
<your-next-app>/
  middleware.ts
  src/
    app/
      api/aurora/[...path]/route.ts
      agents/welcome/page.tsx
    components/ChatStream.tsx
    lib/fetch.ts
```

2) Add environment variable in `.env.local`:

```
FASTAPI_URL=http://localhost:8000
```

3) Start your app:

```
npm run dev
# visit http://localhost:3000/agents/welcome
```

4) (Optional) If your backend sets a **JWT cookie** (recommended):
   - Name: `aurora_token` (or adjust in `middleware.ts`)
   - Flags: `HttpOnly; Secure; SameSite=Strict; Path=/`
   - Frontend requests already use `credentials: "include"`

5) (Optional) CSRF for unsafe methods:
   - Issue a `csrf_token` cookie from backend and mirror it in `x-csrf-token` header on POST/PUT/DELETE.
   - Validate on the backend. (The streaming call already sends JSON; add the header if enabled.)

---

## Notes

- The proxy route (`/api/aurora/*`) hides your backend origin and avoids browser‑side CORS issues.
- The streaming UI uses `ReadableStream` in the browser and progressively appends tokens as they arrive.
- You can style everything with Tailwind; the classes are included but harmless if Tailwind isn’t set up yet.
- This drop‑in doesn’t modify your `layout.tsx` — it should “just work” inside your existing app shell.
