import { NextRequest, NextResponse } from "next/server";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function authenticatedFetch(
  request: NextRequest,
  endpoint: string,
  options: RequestInit = {}
): Promise<Response> {
  // Get token from cookie
  const token = request.cookies.get("access_token")?.value;
  const refreshToken = request.cookies.get("refresh_token")?.value;

  if (!token && !refreshToken) {
    return new Response(JSON.stringify({ error: "Unauthorized" }), {
      status: 401,
      headers: { "Content-Type": "application/json" },
    });
  }

  // Merge headers with Authorization
  const headers = {
    ...options.headers,
    Authorization: `Bearer ${token}`,
  };

  // First attempt - make request to backend
  let response = await fetch(`${API_URL}${endpoint}`, {
    ...options,
    headers,
  });

  const data = await response.json();
  const nextResponse = NextResponse.json(data, { status: response.status });
  return nextResponse;
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
