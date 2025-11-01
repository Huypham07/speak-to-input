import { NextRequest, NextResponse } from "next/server";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

/**
 * Wrapper for authenticated API calls
 * Automatically adds Authorization header from request cookies
 */
export async function authenticatedFetch(
  request: NextRequest,
  endpoint: string,
  options: RequestInit = {}
): Promise<Response> {
  // Get token from cookie or Authorization header
  const token =
    request.cookies.get("access_token")?.value || request.headers.get("authorization")?.replace("Bearer ", "");

  if (!token) {
    return new Response(JSON.stringify({ error: "Unauthorized" }), {
      status: 401,
      headers: { "Content-Type": "application/json" },
    });
  }

  // Merge headers
  const headers = {
    ...options.headers,
    Authorization: `Bearer ${token}`,
  };

  // Make request to backend
  return fetch(`${API_URL}${endpoint}`, {
    ...options,
    headers,
  });
}

/**
 * Create a proxy API route that forwards requests to backend with authentication
 */
export function createAuthenticatedRoute(endpoint: string) {
  return {
    async GET(request: NextRequest) {
      try {
        const response = await authenticatedFetch(request, endpoint);
        const data = await response.json();

        if (!response.ok) {
          return NextResponse.json({ error: data.detail || "Request failed" }, { status: response.status });
        }

        return NextResponse.json(data);
      } catch (error) {
        console.error("API route error:", error);
        return NextResponse.json({ error: "Internal server error" }, { status: 500 });
      }
    },

    async POST(request: NextRequest) {
      try {
        const body = await request.json();
        const response = await authenticatedFetch(request, endpoint, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(body),
        });

        const data = await response.json();

        if (!response.ok) {
          return NextResponse.json({ error: data.detail || "Request failed" }, { status: response.status });
        }

        return NextResponse.json(data);
      } catch (error) {
        console.error("API route error:", error);
        return NextResponse.json({ error: "Internal server error" }, { status: 500 });
      }
    },

    async PUT(request: NextRequest) {
      try {
        const body = await request.json();
        const response = await authenticatedFetch(request, endpoint, {
          method: "PUT",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(body),
        });

        const data = await response.json();

        if (!response.ok) {
          return NextResponse.json({ error: data.detail || "Request failed" }, { status: response.status });
        }

        return NextResponse.json(data);
      } catch (error) {
        console.error("API route error:", error);
        return NextResponse.json({ error: "Internal server error" }, { status: 500 });
      }
    },

    async DELETE(request: NextRequest) {
      try {
        const response = await authenticatedFetch(request, endpoint, {
          method: "DELETE",
        });

        if (response.status === 204) {
          return new NextResponse(null, { status: 204 });
        }

        const data = await response.json();

        if (!response.ok) {
          return NextResponse.json({ error: data.detail || "Request failed" }, { status: response.status });
        }

        return NextResponse.json(data);
      } catch (error) {
        console.error("API route error:", error);
        return NextResponse.json({ error: "Internal server error" }, { status: 500 });
      }
    },
  };
}
