/**
 * Authentication Context — No-op (always authenticated)
 * Auth system removed. This stub keeps useAuth() imports working.
 */

/* eslint-disable react-refresh/only-export-components */

import {
  createContext,
  useContext,
  type ReactNode,
} from "react";
import type { User, UserUpdate } from "@/lib/api";

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (email: string, password: string, rememberMe?: boolean) => Promise<User>;
  signup: (email: string, password: string, name?: string) => Promise<User>;
  updateProfile: (data: UserUpdate) => Promise<User>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

// Default user (always logged in)
const DEFAULT_USER: User = {
  id: 1,
  email: "user@velocity.ai",
  name: "Velocity User",
  token: "local-dev",
  created_at: new Date().toISOString(),
};

export function AuthProvider({ children }: { children: ReactNode }) {
  const value: AuthContextType = {
    user: DEFAULT_USER,
    isLoading: false,
    isAuthenticated: true,
    login: async () => DEFAULT_USER,
    signup: async () => DEFAULT_USER,
    updateProfile: async () => DEFAULT_USER,
    logout: () => {},
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);
  if (context === undefined) {
    // Return default when used outside provider
    return {
      user: DEFAULT_USER,
      isLoading: false,
      isAuthenticated: true,
      login: async () => DEFAULT_USER,
      signup: async () => DEFAULT_USER,
      updateProfile: async () => DEFAULT_USER,
      logout: () => {},
    };
  }
  return context;
}

export default AuthContext;
