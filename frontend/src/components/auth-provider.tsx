"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";

import {
  AUTH_EXPIRED_EVENT,
  api,
  getAccessToken,
  setAccessToken,
} from "@/lib/api";
import type { Application, AuthStatus, User } from "@/types";

type AuthContextValue = {
  user: User | null;
  loading: boolean;
  authStatus: AuthStatus | NoneAuth;
  applications: Application[];
  appliedUrls: Set<string>;
  signInWithGoogleToken: (idToken: string) => Promise<void>;
  signOut: () => void;
  refreshApplications: () => Promise<void>;
  markApplied: (application: Application) => void;
};

type NoneAuth = {
  google_login_enabled: boolean;
  google_client_id: string;
};

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [authStatus, setAuthStatus] = useState<NoneAuth>({
    google_login_enabled: false,
    google_client_id: "",
  });
  const [applications, setApplications] = useState<Application[]>([]);

  const refreshApplications = useCallback(async () => {
    if (!getAccessToken()) {
      setApplications([]);
      return;
    }
    try {
      const data = await api.listApplications();
      setApplications(data.applications);
    } catch {
      setApplications([]);
    }
  }, []);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const status = await api.getAuthStatus();
        if (!cancelled) setAuthStatus(status);
      } catch {
        // backend may be down during boot
      }

      const token = getAccessToken();
      if (!token) {
        if (!cancelled) setLoading(false);
        return;
      }
      try {
        const me = await api.getMe();
        if (!cancelled) {
          setUser(me);
          await refreshApplications();
        }
      } catch {
        setAccessToken(null);
        if (!cancelled) setUser(null);
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [refreshApplications]);

  useEffect(() => {
    function onExpired() {
      setUser(null);
      setApplications([]);
    }
    window.addEventListener(AUTH_EXPIRED_EVENT, onExpired);
    return () => window.removeEventListener(AUTH_EXPIRED_EVENT, onExpired);
  }, []);

  const signInWithGoogleToken = useCallback(
    async (idToken: string) => {
      const data = await api.loginWithGoogle(idToken);
      setAccessToken(data.access_token);
      setUser(data.user);
      await refreshApplications();
    },
    [refreshApplications]
  );

  const signOut = useCallback(() => {
    setAccessToken(null);
    setUser(null);
    setApplications([]);
  }, []);

  const markApplied = useCallback((application: Application) => {
    setApplications((prev) => {
      if (prev.some((row) => row.job_url === application.job_url)) return prev;
      return [application, ...prev];
    });
  }, []);

  const appliedUrls = useMemo(
    () => new Set(applications.map((row) => row.job_url)),
    [applications]
  );

  const value = useMemo(
    () => ({
      user,
      loading,
      authStatus,
      applications,
      appliedUrls,
      signInWithGoogleToken,
      signOut,
      refreshApplications,
      markApplied,
    }),
    [
      user,
      loading,
      authStatus,
      applications,
      appliedUrls,
      signInWithGoogleToken,
      signOut,
      refreshApplications,
      markApplied,
    ]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
