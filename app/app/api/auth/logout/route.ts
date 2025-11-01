import { NextRequest, NextResponse } from "next/server";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function POST(request: NextRequest) {
  try {
    // Call backend logout
    const response = await fetch(`${API_URL}/api/v1/auth/logout`, {
      method: "POST",
      headers: {
        Cookie: request.headers.get("cookie") || "",
      },
    });

    if (!response.ok) {
      return NextResponse.json({ error: "Logout failed" }, { status: response.status });
    }

    // Create response
    const data = await response.json();
    const nextResponse = NextResponse.json(data);

    nextResponse.cookies.delete("access_token");
    nextResponse.cookies.delete("refresh_token");

    // Also forward Set-Cookie headers from backend
    const setCookieHeaders = response.headers.get("set-cookie");
    if (setCookieHeaders) {
      nextResponse.headers.set("Set-Cookie", setCookieHeaders);
    }

    return nextResponse;
  } catch (error) {
    console.error("Logout error:", error);
    return NextResponse.json({ error: "Internal server error" }, { status: 500 });
  }
}
