"use client";

import React, { createContext, useContext, useEffect, useState, useCallback } from "react";
import axios from "axios";
import { useRouter } from "next/navigation";

export type AuthUser = {
  id: string;
  email: string;
  role: "admin" | "user";
  is_active: boolean;
};

type AuthContextType = {
  user: AuthUser | null;
  token: string | null;
  loading: boolean;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
};

const AuthContext = createContext<AuthContextType>({
  user: null,
  token: null,
  loading: true,
  logout: async () => {},
  refreshUser: async () => {},
});

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  const refreshUser = useCallback(async () => {
    try {
      const [meRes, tokenRes] = await Promise.all([
        axios.get("/api/auth/me"),
        axios.get("/api/auth/token"),
      ]);
      setUser(meRes.data);
      setToken(tokenRes.data.token);
    } catch {
      setUser(null);
      setToken(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refreshUser();
  }, [refreshUser]);

  const logout = useCallback(async () => {
    try {
      await axios.post("/api/auth/logout");
    } finally {
      setUser(null);
      setToken(null);
      router.push("/auth/login");
    }
  }, [router]);

  return (
    <AuthContext.Provider value={{ user, token, loading, logout, refreshUser }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
