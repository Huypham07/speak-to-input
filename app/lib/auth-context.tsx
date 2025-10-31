"use client";

import type React from "react";
import { createContext, useContext, useState, useCallback, useEffect } from "react";

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
  const [isLoading, setIsLoading] = useState(false);
  const [token, setToken] = useState<string | null>(null);

  // Load token from localStorage on mount
  useEffect(() => {
    const storedToken = localStorage.getItem("access_token");
    if (storedToken) {
      setToken(storedToken);
      // Fetch user info
      fetchUserInfo(storedToken);
    }
  }, []);

  const fetchUserInfo = async (accessToken: string) => {
    try {
      const response = await fetch("/api/auth/me", {
        headers: {
          Authorization: `Bearer ${accessToken}`,
        },
      });

      if (response.ok) {
        const userData = await response.json();
        setUser(userData);
      } else {
        // Token invalid, clear it
        localStorage.removeItem("access_token");
        setToken(null);
      }
    } catch (error) {
      console.error("Failed to fetch user info:", error);
      localStorage.removeItem("access_token");
      setToken(null);
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

      // Save token to both localStorage and cookie
      localStorage.setItem("access_token", data.access_token);
      document.cookie = `access_token=${data.access_token}; path=/; max-age=${30 * 24 * 60 * 60}`; // 30 days
      setToken(data.access_token);

      // Fetch user info
      await fetchUserInfo(data.access_token);
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
    localStorage.removeItem("access_token");
    document.cookie = "access_token=; path=/; max-age=0"; // Clear cookie
    setToken(null);
    setUser(null);
  }, []);

  return <AuthContext.Provider value={{ user, isLoading, login, signup, logout }}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return context;
}
