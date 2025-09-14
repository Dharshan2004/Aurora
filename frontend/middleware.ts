import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

/**
 * Middleware for demo deployment - authentication disabled for easier testing.
 * For production, implement proper JWT authentication flow.
 */
export function middleware(req: NextRequest) {
  // Skip authentication for demo deployment
  // TODO: Implement proper authentication for production
  return NextResponse.next();
}

export const config = {
  // Disable middleware matcher for demo - all routes are accessible
  matcher: [],
};
