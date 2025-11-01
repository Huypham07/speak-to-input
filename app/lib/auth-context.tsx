"use client";

import type React from "react";
import { createContext, useContext, useState, useCallback, useEffect } from "react";
import { useRouter } from "next/navigation";

interface User {
  id: number;
  username: string;
  email: string;
  full_name: string | null;
  is_active: boolean;
  is_verified: boolean;
}

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  login: (username: string, password: string) => Promise<void>;
  signup: (username: string, email: string, password: string, fullName?: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true); // Start with TRUE to prevent premature redirects
  const router = useRouter();

  // Check authentication on mount
  useEffect(() => {
    fetchUserInfo();
  }, []);

  const fetchUserInfo = async () => {
    setIsLoading(true); // Start loading
    try {
      // No need to pass token - cookie will be sent automatically
      const response = await fetch("/api/auth/me");

      if (response.ok) {
        const userData = await response.json();
        setUser(userData);
      } else if (response.status === 401) {
        // Token expired, try to refresh using refresh token from cookie
        console.log("Access token expired, attempting refresh...");
        const refreshed = await refreshAccessToken();
        if (refreshed) {
          // Retry fetching user info
          const retryResponse = await fetch("/api/auth/me");
          if (retryResponse.ok) {
            const userData = await retryResponse.json();
            setUser(userData);
            return;
          }
        }
        // Refresh failed, clear user
        setUser(null);
      } else {
        // Other errors
        setUser(null);
      }
    } catch (error) {
      console.error("Failed to fetch user info:", error);
      setUser(null);
    } finally {
      setIsLoading(false); // Done loading
    }
  };

  const refreshAccessToken = async (): Promise<boolean> => {
    try {
      // Refresh endpoint reads refresh_token from httpOnly cookie
      const response = await fetch("/api/auth/refresh", {
        method: "POST",
        credentials: "include", // Send cookies
      });

      if (response.ok) {
        return true;
      } else {
        console.error("Failed to refresh token");
        return false;
      }
    } catch (error) {
      console.error("Error refreshing token:", error);
      return false;
    }
  };

  const login = useCallback(async (username: string, password: string) => {
    setIsLoading(true);
    try {
      const response = await fetch("/api/auth/login", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ username, password }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || "Login failed");
      }

      // Cookies are set by backend, just fetch user info
      await fetchUserInfo();
    } finally {
      setIsLoading(false);
    }
  }, []);

  const signup = useCallback(
    async (username: string, email: string, password: string, fullName?: string) => {
      setIsLoading(true);
      try {
        const response = await fetch("/api/auth/register", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            username,
            email,
            password,
            full_name: fullName || null,
          }),
        });

        const data = await response.json();

        if (!response.ok) {
          throw new Error(data.error || "Registration failed");
        }

        // Auto login after signup
        await login(username, password);
      } finally {
        setIsLoading(false);
      }
    },
    [login]
  );

  const logout = useCallback(() => {
    // Cookie will be cleared by calling backend logout endpoint
    fetch("/api/auth/logout", { method: "POST" }).catch(console.error);
    setUser(null);
    router.push("/login");
  }, [router]);

  return <AuthContext.Provider value={{ user, isLoading, login, signup, logout }}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return context;
}
