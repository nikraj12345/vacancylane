"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import {
  Building2,
  ExternalLink,
  LoaderCircle,
  MapPin,
  Trash2,
} from "lucide-react";

import { AppShell } from "@/components/app-shell";
import { useAuth } from "@/components/auth-provider";
import { api } from "@/lib/api";
import { cn } from "@/lib/utils";

const STATUSES = [
  "applied",
  "interviewing",
  "offer",
  "rejected",
  "withdrawn",
] as const;

export default function ApplicationsPage() {
  const { user, loading, applications, refreshApplications } = useAuth();
  const [filter, setFilter] = useState<string>("all");
  const [busyId, setBusyId] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

  const visible = useMemo(() => {
    if (filter === "all") return applications;
    return applications.filter((row) => row.status === filter);
  }, [applications, filter]);

  async function setStatus(id: number, status: string) {
    setBusyId(id);
    setError(null);
    try {
      await api.updateApplication(id, { status });
      await refreshApplications();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Update failed");
    } finally {
      setBusyId(null);
    }
  }

  async function remove(id: number) {
    setBusyId(id);
    setError(null);
    try {
      await api.deleteApplication(id);
      await refreshApplications();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Remove failed");
    } finally {
      setBusyId(null);
    }
  }

  return (
    <AppShell>
      <main className="relative mx-auto max-w-5xl px-4 py-8 sm:px-6">
        <div className="mb-8">
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-emerald-400">
            Tracker
          </p>
          <h1 className="mt-2 font-[family-name:var(--font-display)] text-3xl font-semibold tracking-tight text-white">
            Applied jobs
          </h1>
          <p className="mt-2 text-sm text-slate-500">
            Every role you marked Apply from search lands here with status tracking.
          </p>
        </div>

        {loading ? (
          <div className="flex justify-center py-20">
            <LoaderCircle className="h-7 w-7 animate-spin text-emerald-400" />
          </div>
        ) : !user ? (
          <div className="rounded-2xl border border-white/8 bg-white/[0.03] px-6 py-16 text-center">
            <p className="font-medium text-white">Sign in to track applications</p>
            <p className="mt-2 text-sm text-slate-500">
              Google login keeps your applied list private to your account.
            </p>
            <Link
              href="/login"
              className="mt-6 inline-flex rounded-xl bg-emerald-400 px-5 py-2.5 text-sm font-semibold text-[#07100c] hover:bg-emerald-300"
            >
              Sign in
            </Link>
          </div>
        ) : (
          <>
            <div className="mb-5 flex flex-wrap gap-2">
              {["all", ...STATUSES].map((status) => (
                <button
                  key={status}
                  type="button"
                  onClick={() => setFilter(status)}
                  className={cn(
                    "rounded-lg border px-3 py-1.5 text-xs capitalize transition",
                    filter === status
                      ? "border-emerald-400/30 bg-emerald-400/10 text-emerald-200"
                      : "border-white/8 text-slate-500 hover:bg-white/5"
                  )}
                >
                  {status}
                  {status === "all" ? ` · ${applications.length}` : ""}
                </button>
              ))}
            </div>

            {error && (
              <p className="mb-4 rounded-lg border border-rose-400/20 bg-rose-500/10 px-3 py-2 text-xs text-rose-300">
                {error}
              </p>
            )}

            {visible.length === 0 ? (
              <div className="rounded-2xl border border-dashed border-white/10 px-6 py-16 text-center">
                <p className="text-sm text-slate-400">No applications in this view yet.</p>
                <Link
                  href="/search"
                  className="mt-4 inline-flex text-sm text-emerald-400 hover:text-emerald-300"
                >
                  Search open roles →
                </Link>
              </div>
            ) : (
              <ul className="space-y-3">
                {visible.map((row) => (
                  <li
                    key={row.id}
                    className="rounded-2xl border border-white/8 bg-white/[0.03] p-4 sm:p-5"
                  >
                    <div className="flex flex-wrap items-start gap-4">
                      <div className="min-w-0 flex-1">
                        <a
                          href={row.job_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-base font-semibold text-slate-100 hover:text-emerald-300"
                        >
                          {row.job_title}
                        </a>
                        <div className="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-xs text-slate-500">
                          {row.company && (
                            <span className="inline-flex items-center gap-1.5">
                              <Building2 className="h-3.5 w-3.5" />
                              {row.company}
                            </span>
                          )}
                          {row.location && (
                            <span className="inline-flex items-center gap-1.5">
                              <MapPin className="h-3.5 w-3.5" />
                              {row.location}
                            </span>
                          )}
                          <span>
                            Applied {new Date(row.applied_at).toLocaleString()}
                          </span>
                        </div>
                      </div>
                      <div className="flex flex-wrap items-center gap-2">
                        <select
                          value={row.status}
                          disabled={busyId === row.id}
                          onChange={(e) => setStatus(row.id, e.target.value)}
                          className="rounded-lg border border-white/10 bg-[#101411] px-2.5 py-2 text-xs text-slate-200"
                        >
                          {STATUSES.map((status) => (
                            <option key={status} value={status}>
                              {status}
                            </option>
                          ))}
                        </select>
                        <a
                          href={row.job_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center gap-1 rounded-lg border border-white/10 px-2.5 py-2 text-xs text-slate-300 hover:bg-white/5"
                        >
                          Open
                          <ExternalLink className="h-3 w-3" />
                        </a>
                        <button
                          type="button"
                          disabled={busyId === row.id}
                          onClick={() => remove(row.id)}
                          className="inline-flex items-center gap-1 rounded-lg border border-rose-400/20 px-2.5 py-2 text-xs text-rose-300 hover:bg-rose-500/10 disabled:opacity-50"
                        >
                          <Trash2 className="h-3.5 w-3.5" />
                          Remove
                        </button>
                      </div>
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </>
        )}
      </main>
    </AppShell>
  );
}
