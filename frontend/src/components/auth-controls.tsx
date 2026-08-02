"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { LoaderCircle, LogIn, LogOut } from "lucide-react";

import { useAuth } from "@/components/auth-provider";
import { cn } from "@/lib/utils";

declare global {
  interface Window {
    google?: {
      accounts: {
        id: {
          initialize: (config: Record<string, unknown>) => void;
          prompt: (
            callback?: (notification: {
              isNotDisplayed: () => boolean;
              isSkippedMoment: () => boolean;
            }) => void
          ) => void;
          renderButton: (
            parent: HTMLElement,
            config: Record<string, unknown>
          ) => void;
          cancel: () => void;
        };
      };
    };
  }
}

const GIS_SRC = "https://accounts.google.com/gsi/client";

function loadGoogleScript(): Promise<void> {
  if (typeof window === "undefined") return Promise.resolve();
  if (window.google?.accounts?.id) return Promise.resolve();
  const existing = document.querySelector<HTMLScriptElement>(
    `script[src="${GIS_SRC}"]`
  );
  if (existing) {
    return new Promise((resolve, reject) => {
      if (window.google?.accounts?.id) {
        resolve();
        return;
      }
      existing.addEventListener("load", () => resolve());
      existing.addEventListener("error", () =>
        reject(new Error("Failed to load Google Sign-In"))
      );
    });
  }
  return new Promise((resolve, reject) => {
    const script = document.createElement("script");
    script.src = GIS_SRC;
    script.async = true;
    script.defer = true;
    script.onload = () => resolve();
    script.onerror = () => reject(new Error("Failed to load Google Sign-In"));
    document.head.appendChild(script);
  });
}

type GoogleButtonProps = {
  /** Larger button for /login and /signup */
  variant?: "header" | "page";
  className?: string;
  onSignedIn?: () => void;
};

/**
 * Renders Google's official Sign in with Google button and exchanges the
 * ID token for a Vacancylane session.
 */
export function GoogleSignInButton({
  variant = "header",
  className,
  onSignedIn,
}: GoogleButtonProps) {
  const { user, loading, authStatus, signInWithGoogleToken } = useAuth();
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [hostReady, setHostReady] = useState(false);
  const buttonHost = useRef<HTMLDivElement | null>(null);

  const setHost = useCallback((node: HTMLDivElement | null) => {
    buttonHost.current = node;
    setHostReady(Boolean(node));
  }, []);

  const handleCredential = useCallback(
    async (response: { credential?: string }) => {
      if (!response.credential) return;
      setBusy(true);
      setError(null);
      try {
        await signInWithGoogleToken(response.credential);
        onSignedIn?.();
      } catch (err) {
        setError(err instanceof Error ? err.message : "Google sign-in failed");
      } finally {
        setBusy(false);
      }
    },
    [onSignedIn, signInWithGoogleToken]
  );

  useEffect(() => {
    if (loading || user) return;
    if (!authStatus.google_login_enabled || !authStatus.google_client_id) return;
    if (!hostReady || !buttonHost.current) return;

    let cancelled = false;
    (async () => {
      try {
        await loadGoogleScript();
        if (cancelled || !window.google?.accounts?.id || !buttonHost.current) {
          return;
        }
        window.google.accounts.id.initialize({
          client_id: authStatus.google_client_id,
          callback: handleCredential,
          auto_select: false,
          cancel_on_tap_outside: true,
          use_fedcm_for_prompt: true,
        });
        buttonHost.current.innerHTML = "";
        window.google.accounts.id.renderButton(buttonHost.current, {
          theme: variant === "page" ? "outline" : "filled_black",
          size: "large",
          shape: "pill",
          text: "continue_with",
          logo_alignment: "left",
          width: variant === "page" ? 320 : 180,
        });
      } catch (err) {
        if (!cancelled) {
          setError(
            err instanceof Error ? err.message : "Google Sign-In unavailable"
          );
        }
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [
    authStatus.google_client_id,
    authStatus.google_login_enabled,
    handleCredential,
    hostReady,
    loading,
    user,
    variant,
  ]);

  if (loading) {
    return (
      <div
        className={cn(
          "flex items-center justify-center rounded-full bg-white/5",
          variant === "page" ? "h-12 w-full" : "h-9 w-28",
          className
        )}
      >
        <LoaderCircle className="h-4 w-4 animate-spin text-slate-500" />
      </div>
    );
  }

  if (user) return null;

  if (!authStatus.google_login_enabled) {
    return (
      <div
        title="Set GOOGLE_OAUTH_CLIENT_ID in the backend .env"
        className={cn(
          "inline-flex items-center gap-1.5 rounded-lg border border-amber-400/20 bg-amber-500/10 px-2.5 py-2 text-[11px] text-amber-200",
          className
        )}
      >
        <LogIn className="h-3.5 w-3.5" />
        Google login off
      </div>
    );
  }

  return (
    <div
      className={cn(
        "flex flex-col",
        variant === "page" ? "items-stretch gap-2" : "items-end gap-1",
        className
      )}
    >
      <div
        ref={setHost}
        className={cn(
          "flex min-h-10 items-center justify-center",
          variant === "page" && "w-full [&_iframe]:!w-full",
          busy && "pointer-events-none opacity-60"
        )}
      />
      {busy && (
        <p className="text-center text-[11px] text-slate-500">
          Signing you in with Google…
        </p>
      )}
      {error && (
        <p
          className={cn(
            "text-[11px] text-rose-300",
            variant === "page" ? "text-center" : "max-w-[14rem] text-right"
          )}
        >
          {error}
        </p>
      )}
    </div>
  );
}

/** Compact header control: Google button when signed out, profile when signed in. */
export function AuthControls() {
  const { user, loading, applications, signOut } = useAuth();

  if (loading) {
    return <div className="h-9 w-28 animate-pulse rounded-full bg-white/5" />;
  }

  if (user) {
    return (
      <div className="flex items-center gap-2">
        <div className="hidden items-center gap-2 rounded-full border border-white/10 bg-white/[0.04] py-1 pl-1 pr-3 sm:flex">
          {user.picture_url ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img
              src={user.picture_url}
              alt=""
              className="h-7 w-7 rounded-full"
              referrerPolicy="no-referrer"
            />
          ) : (
            <div className="flex h-7 w-7 items-center justify-center rounded-full bg-emerald-400 text-[11px] font-bold text-[#07100c]">
              {(user.name || user.email).slice(0, 1).toUpperCase()}
            </div>
          )}
          <div className="min-w-0">
            <p className="truncate text-xs font-medium text-white">
              {user.name || user.email}
            </p>
            <p className="text-[10px] text-slate-500">
              {applications.length} applied
            </p>
          </div>
        </div>
        <button
          type="button"
          onClick={signOut}
          className="inline-flex items-center gap-1.5 rounded-lg border border-white/10 px-2.5 py-2 text-xs text-slate-300 transition hover:bg-white/5"
        >
          <LogOut className="h-3.5 w-3.5" />
          Sign out
        </button>
      </div>
    );
  }

  return <GoogleSignInButton variant="header" />;
}
