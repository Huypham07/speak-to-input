import { NextRequest, NextResponse } from "next/server";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function refreshAccessToken(request: NextRequest): Promise<{
  success: boolean;
  newToken?: string;
  setCookie?: string;
}> {
  try {
    const refreshToken = request.cookies.get("refresh_token")?.value;

    if (!refreshToken) {
      return { success: false };
    }

    const response = await fetch(`${API_URL}/api/v1/auth/refresh`, {
      method: "POST",
      headers: {
        Cookie: `refresh_token=${refreshToken}`,
      },
    });

    if (response.ok) {
      const data = await response.json();
      const setCookieHeader = response.headers.get("set-cookie");

      return {
        success: true,
        newToken: data.access_token,
        setCookie: setCookieHeader || undefined,
      };
    }

    return { success: false };
  } catch (error) {
    console.error("Token refresh failed:", error);
    return { success: false };
  }
}

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

  // If 401, try to refresh token and retry ONCE
  if (response.status === 401) {
    const refreshResult = await refreshAccessToken(request);

    if (refreshResult.success && refreshResult.newToken) {
      // Retry with new token
      response = await fetch(`${API_URL}${endpoint}`, {
        ...options,
        headers: {
          ...options.headers,
          Authorization: `Bearer ${refreshResult.newToken}`,
        },
      });
    }
  }

  return response;
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
