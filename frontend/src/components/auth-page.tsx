"use client";

import { useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  ArrowLeft,
  BriefcaseBusiness,
  CheckCircle2,
  FileSearch,
  LockKeyhole,
  MapPin,
  ShieldCheck,
  Sparkles,
} from "lucide-react";

import { GoogleSignInButton } from "@/components/auth-controls";
import { useAuth } from "@/components/auth-provider";

type AuthMode = "login" | "signin" | "signup";

const benefits = [
  { icon: FileSearch, text: "Search directly from your resume" },
  { icon: MapPin, text: "See relevant locations first" },
  { icon: CheckCircle2, text: "Track every application automatically" },
];

export function AuthPage({ mode }: { mode: AuthMode }) {
  const router = useRouter();
  const { user, loading, authStatus } = useAuth();
  const isSignup = mode === "signup";

  useEffect(() => {
    if (!loading && user) router.replace("/search");
  }, [loading, router, user]);

  function goToSearch() {
    router.replace("/search");
  }

  return (
    <main className="relative min-h-screen overflow-hidden bg-[#080a09] text-white">
      <div className="landing-grid pointer-events-none fixed inset-0 opacity-40" />
      <div className="landing-orb landing-orb-one" />
      <div className="landing-orb landing-orb-two" />

      <div className="relative z-10 grid min-h-screen lg:grid-cols-[1.05fr_.95fr]">
        <section className="hidden border-r border-white/[0.07] p-12 lg:flex lg:flex-col">
          <Link href="/" className="flex items-center gap-3 self-start">
            <span className="flex h-10 w-10 items-center justify-center rounded-xl border border-emerald-300/20 bg-emerald-400 text-[#07100c] shadow-lg shadow-emerald-950/40">
              <BriefcaseBusiness className="h-5 w-5" />
            </span>
            <span className="text-lg font-semibold tracking-tight">Vacancylane</span>
          </Link>

          <div className="my-auto max-w-xl landing-rise">
            <span className="mb-6 inline-flex items-center gap-2 rounded-full border border-emerald-400/20 bg-emerald-400/8 px-3 py-1.5 text-xs text-emerald-200">
              <Sparkles className="h-3.5 w-3.5" />
              A clearer path to your next role
            </span>
            <h1 className="text-5xl font-semibold leading-[1.08] tracking-[-0.04em]">
              Search smarter.
              <span className="landing-gradient-text block">Apply with confidence.</span>
            </h1>
            <p className="mt-5 max-w-lg text-base leading-7 text-slate-400">
              One account keeps your job discovery and application history
              together without hiding opportunities behind a paywall.
            </p>
            <div className="mt-10 space-y-4">
              {benefits.map(({ icon: Icon, text }, index) => (
                <div
                  key={text}
                  className="landing-result flex items-center gap-3 text-sm text-slate-300"
                  style={{ animationDelay: `${0.25 + index * 0.12}s` }}
                >
                  <span className="flex h-9 w-9 items-center justify-center rounded-xl border border-white/8 bg-white/[0.04] text-emerald-300">
                    <Icon className="h-4 w-4" />
                  </span>
                  {text}
                </div>
              ))}
            </div>
          </div>

          <p className="text-xs text-slate-600">
            Your account is secured by Google. Vacancylane never sees your password.
          </p>
        </section>

        <section className="flex min-h-screen items-center justify-center px-5 py-12 sm:px-8">
          <div className="landing-rise landing-delay w-full max-w-md">
            <Link
              href="/"
              className="mb-8 inline-flex items-center gap-2 text-sm text-slate-500 transition hover:text-slate-200 lg:hidden"
            >
              <ArrowLeft className="h-4 w-4" />
              Back to Vacancylane
            </Link>

            <div className="rounded-3xl border border-white/10 bg-[#0d100e]/92 p-6 shadow-2xl shadow-black/40 backdrop-blur-xl sm:p-8">
              <div className="mb-7 flex rounded-xl border border-white/8 bg-black/20 p-1">
                <Link
                  href="/login"
                  className={`flex-1 rounded-lg px-3 py-2 text-center text-sm transition ${
                    !isSignup
                      ? "bg-white/[0.08] font-medium text-white shadow"
                      : "text-slate-500 hover:text-slate-300"
                  }`}
                >
                  Sign in
                </Link>
                <Link
                  href="/signup"
                  className={`flex-1 rounded-lg px-3 py-2 text-center text-sm transition ${
                    isSignup
                      ? "bg-white/[0.08] font-medium text-white shadow"
                      : "text-slate-500 hover:text-slate-300"
                  }`}
                >
                  Sign up
                </Link>
              </div>

              <h2 className="text-2xl font-semibold tracking-tight">
                {isSignup ? "Create your free account" : "Welcome back"}
              </h2>
              <p className="mt-2 text-sm leading-6 text-slate-500">
                {isSignup
                  ? "Start searching and keep every application organized."
                  : "Continue to your job search and application tracker."}
              </p>

              <div className="mt-7 space-y-3">
                <p className="text-center text-xs font-medium uppercase tracking-[0.16em] text-slate-500">
                  {isSignup ? "Sign up with Google" : "Sign in with Google"}
                </p>
                <div className="rounded-xl border border-white/8 bg-white/[0.025] p-4">
                  <GoogleSignInButton
                    variant="page"
                    onSignedIn={goToSearch}
                  />
                </div>
                <p className="text-center text-[11px] leading-5 text-slate-600">
                  Same Google account works for both sign in and sign up —
                  we create your Vacancylane profile the first time you continue.
                </p>
              </div>

              {!loading && !authStatus.google_login_enabled && (
                <p className="mt-3 rounded-lg border border-amber-400/15 bg-amber-500/[0.06] px-3 py-2 text-xs leading-5 text-amber-200/80">
                  Google login needs its OAuth client ID configured before this
                  page can accept sign-ins.
                </p>
              )}

              <div className="my-6 flex items-center gap-3">
                <span className="h-px flex-1 bg-white/8" />
                <span className="text-[10px] uppercase tracking-[0.18em] text-slate-600">
                  Secure account
                </span>
                <span className="h-px flex-1 bg-white/8" />
              </div>

              <div className="flex items-start gap-3 rounded-xl border border-emerald-400/10 bg-emerald-500/[0.04] p-3">
                <LockKeyhole className="mt-0.5 h-4 w-4 shrink-0 text-emerald-400" />
                <p className="text-xs leading-5 text-slate-500">
                  We use Google only to verify your identity. Your searches and
                  application history are private to your account.
                </p>
              </div>

              <p className="mt-6 text-center text-xs leading-5 text-slate-600">
                By continuing, you agree to use Vacancylane for legitimate job
                discovery and application tracking.
              </p>
            </div>

            <div className="mt-6 flex items-center justify-center gap-2 text-xs text-slate-600">
              <ShieldCheck className="h-3.5 w-3.5 text-emerald-500/70" />
              Google verified · Password-free · Free to use
            </div>
          </div>
        </section>
      </div>
    </main>
  );
}
