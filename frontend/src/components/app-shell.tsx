"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  BriefcaseBusiness,
  CheckCircle2,
  History,
  Search,
} from "lucide-react";

import { AuthControls } from "@/components/auth-controls";
import { useAuth } from "@/components/auth-provider";
import { cn } from "@/lib/utils";

const NAV = [
  { href: "/search", label: "Search", icon: Search },
  { href: "/applications", label: "Applied", icon: CheckCircle2 },
  { href: "/history", label: "History", icon: History },
];

export function AppShell({
  children,
  bare = false,
}: {
  children: React.ReactNode;
  bare?: boolean;
}) {
  const pathname = usePathname();
  const { user, applications } = useAuth();

  return (
    <div className="min-h-screen bg-[#090b0a] text-slate-200">
      <div className="pointer-events-none fixed inset-x-0 top-0 h-[420px] bg-[radial-gradient(circle_at_50%_-20%,rgba(16,185,129,.12),transparent_60%)]" />
      <header className="relative z-30 border-b border-white/8 bg-[#0c0f0d]/90 backdrop-blur-xl">
        <div className="mx-auto flex h-16 max-w-7xl items-center justify-between gap-4 px-4 sm:px-6">
          <div className="flex items-center gap-6">
            <Link href="/" className="flex items-center gap-3">
              <span className="flex h-9 w-9 items-center justify-center rounded-xl border border-emerald-300/20 bg-emerald-400 text-[#07100c] shadow-lg shadow-emerald-950/30">
                <BriefcaseBusiness className="h-5 w-5" />
              </span>
              <span className="font-semibold tracking-tight text-white">
                Vacancylane
              </span>
            </Link>
            {!bare && (
              <nav className="hidden items-center gap-1 md:flex">
                {NAV.map(({ href, label, icon: Icon }) => {
                  const active =
                    pathname === href || pathname.startsWith(`${href}/`);
                  return (
                    <Link
                      key={href}
                      href={href}
                      className={cn(
                        "inline-flex items-center gap-1.5 rounded-lg px-3 py-2 text-sm transition",
                        active
                          ? "bg-white/[0.08] text-white"
                          : "text-slate-400 hover:bg-white/[0.04] hover:text-slate-200"
                      )}
                    >
                      <Icon className="h-3.5 w-3.5" />
                      {label}
                      {href === "/applications" && user && applications.length > 0 && (
                        <span className="rounded-full bg-emerald-500/15 px-1.5 text-[10px] font-semibold text-emerald-300">
                          {applications.length}
                        </span>
                      )}
                    </Link>
                  );
                })}
              </nav>
            )}
          </div>
          <div className="flex items-center gap-2">
            {!user && !bare && (
              <Link
                href="/login"
                className="hidden rounded-lg border border-white/10 px-3 py-2 text-xs text-slate-300 transition hover:bg-white/5 sm:inline-flex"
              >
                Sign in
              </Link>
            )}
            <AuthControls />
          </div>
        </div>
        {!bare && (
          <nav className="flex gap-1 overflow-x-auto border-t border-white/5 px-4 py-2 md:hidden">
            {NAV.map(({ href, label, icon: Icon }) => {
              const active = pathname === href || pathname.startsWith(`${href}/`);
              return (
                <Link
                  key={href}
                  href={href}
                  className={cn(
                    "inline-flex shrink-0 items-center gap-1.5 rounded-lg px-3 py-2 text-xs transition",
                    active
                      ? "bg-white/[0.08] text-white"
                      : "text-slate-500 hover:text-slate-300"
                  )}
                >
                  <Icon className="h-3.5 w-3.5" />
                  {label}
                </Link>
              );
            })}
          </nav>
        )}
      </header>
      {children}
    </div>
  );
}
