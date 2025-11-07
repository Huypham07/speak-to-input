export async function refreshAccessToken(): Promise<{
  success: boolean;
  accessToken?: string;
}> {
  try {
    // Call Next.js API route which forwards to backend
    const response = await fetch("/api/auth/refresh", {
      method: "POST",
      credentials: "include",
    });

    if (response.ok) {
      const data = await response.json();

      if (data.access_token) {
        // Update localStorage
        localStorage.setItem("access_token", data.access_token);

        return {
          success: true,
          accessToken: data.access_token,
        };
      }
    }
    return { success: false };
  } catch (error) {
    return { success: false };
  }
}

/**
 * Wrapper for fetch that automatically handles 401 errors by refreshing token
 * and retrying the request once
 */
export async function fetchWithAuth(url: string, options: RequestInit = {}): Promise<Response> {
  // First attempt with current token
  let response = await fetch(url, {
    ...options,
    credentials: "include",
    headers: {
      ...options.headers,
    },
  });

  // If 401, try to refresh and retry once
  if (response.status === 401) {
    const refreshResult = await refreshAccessToken();

    if (refreshResult.success && refreshResult.accessToken) {
      // Retry the original request with new token
      response = await fetch(url, {
        ...options,
        credentials: "include",
        headers: {
          ...options.headers,
        },
      });
    }
  }

  return response;
}
