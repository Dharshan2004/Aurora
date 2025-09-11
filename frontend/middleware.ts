import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

/**
 * Optional middleware to protect agent routes using a JWT stored in an HttpOnly cookie.
 * - Backend should set: Set-Cookie: aurora_token=...; HttpOnly; Secure; SameSite=Strict; Path=/
 * - Adjust 'matcher' as needed or remove this file if you don't need auth for the demo.
 */
export function middleware(req: NextRequest) {
  const jwt = req.cookies.get("aurora_token")?.value;
  const isProtected =
    req.nextUrl.pathname.startsWith("/agents") ||
    req.nextUrl.pathname.startsWith("/dashboard");

  if (isProtected && !jwt) {
    const url = req.nextUrl.clone();
    url.pathname = "/";
    return NextResponse.redirect(url);
  }
  return NextResponse.next();
}

export const config = {
  matcher: ["/agents/:path*", "/dashboard/:path*"],
};
