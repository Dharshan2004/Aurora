import { NextRequest } from "next/server";

// Point this to your FastAPI base URL via .env.local (or Vercel env)
const ORIGIN = process.env.FASTAPI_URL!;

/**
 * Generic forwarder for all /api/aurora/* calls.
 * - Preserves cookies (for JWT-in-cookie auth)
 * - Streams responses (SSE or chunked text)
 * - Avoids exposing your backend origin to the browser
 */
async function forward(req: NextRequest, path: string[], method: string) {
  console.log(`🌐 Frontend Proxy - Method: ${method}, Path: ${path.join("/")}`);
  console.log(`🌐 FASTAPI_URL: ${ORIGIN}`);
  
  if (!ORIGIN) {
    console.log("❌ FASTAPI_URL not set");
    return new Response("FASTAPI_URL environment variable is not set in Vercel. Please set it to your HuggingFace Space URL.", { status: 500 });
  }
  
  // Check if ORIGIN is localhost (common mistake)
  if (ORIGIN.includes('localhost') || ORIGIN.includes('127.0.0.1')) {
    console.log(`❌ FASTAPI_URL is localhost: ${ORIGIN}`);
    return new Response(`FASTAPI_URL is set to localhost (${ORIGIN}). Please set it to your HuggingFace Space URL instead.`, { status: 500 });
  }
  
  const incomingUrl = new URL(req.url);
  const target = `${ORIGIN}/${path.join("/")}${incomingUrl.search}`;
  
  console.log(`🌐 Proxying to: ${target}`);

  // Copy headers, but strip hop-by-hop
  const headers = new Headers(req.headers);
  headers.delete("host");
  headers.delete("connection");
  headers.delete("content-length");

  // Important: do not set 'duplex' in Next route handlers; streaming works by returning res.body directly.
  const res = await fetch(target, {
    method,
    headers,
    body: method === "GET" || method === "HEAD" ? undefined : req.body,
    // Disable caching for dynamic streams
    cache: "no-store",
    // Add duplex option for POST/PUT requests with body
    ...(method !== "GET" && method !== "HEAD" && { duplex: "half" }),
  });

  console.log(`🌐 Backend response status: ${res.status}`);

  // Forward status + stream body and keep most headers
  const outHeaders = new Headers(res.headers);
  // Optionally strip sensitive headers from backend
  outHeaders.delete("content-length");
  outHeaders.delete("transfer-encoding");
  return new Response(res.body, {
    status: res.status,
    statusText: res.statusText,
    headers: outHeaders,
  });
}

export async function GET(req: NextRequest, { params }: { params: Promise<{ path: string[] }> }) {
  const resolvedParams = await params;
  return forward(req, resolvedParams.path, "GET");
}
export async function POST(req: NextRequest, { params }: { params: Promise<{ path: string[] }> }) {
  const resolvedParams = await params;
  return forward(req, resolvedParams.path, "POST");
}
export async function PUT(req: NextRequest, { params }: { params: Promise<{ path: string[] }> }) {
  const resolvedParams = await params;
  return forward(req, resolvedParams.path, "PUT");
}
export async function DELETE(req: NextRequest, { params }: { params: Promise<{ path: string[] }> }) {
  const resolvedParams = await params;
  return forward(req, resolvedParams.path, "DELETE");
}
