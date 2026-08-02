"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  Clock3,
  LoaderCircle,
  RotateCcw,
  Search,
  Trash2,
} from "lucide-react";

import { AppShell } from "@/components/app-shell";
import { useAuth } from "@/components/auth-provider";
import { api } from "@/lib/api";
import type { SavedSearch } from "@/types";

export default function HistoryPage() {
  const router = useRouter();
  const { user, loading: authLoading, signOut } = useAuth();
  const [searches, setSearches] = useState<SavedSearch[]>([]);
  const [loading, setLoading] = useState(true);
  const [busyId, setBusyId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    if (!user) {
      setSearches([]);
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const data = await api.listSearchHistory();
      setSearches(data.searches);
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "Could not load history";
      // Stale sessions show as empty history unless we clear them.
      if (/sign in|unauthorized|invalid or expired|invalid session/i.test(message)) {
        signOut();
        setSearches([]);
        setError("Your session expired. Sign in again to see history.");
      } else {
        setError(message);
      }
    } finally {
      setLoading(false);
    }
  }, [user, signOut]);

  useEffect(() => {
    if (!authLoading) void load();
  }, [authLoading, load]);

  async function remove(id: string) {
    setBusyId(id);
    try {
      await api.deleteSearch(id);
      setSearches((prev) => prev.filter((row) => row.id !== id));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Delete failed");
    } finally {
      setBusyId(null);
    }
  }

  function rerun(row: SavedSearch) {
    try {
      sessionStorage.setItem(
        "vacancylane_rerun",
        JSON.stringify(row.payload || {})
      );
    } catch {
      // ignore storage failures
    }
    router.push("/search?rerun=1");
  }

  return (
    <AppShell>
      <main className="relative mx-auto max-w-5xl px-4 py-8 sm:px-6">
        <div className="mb-8">
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-emerald-400">
            History
          </p>
          <h1 className="mt-2 font-[family-name:var(--font-display)] text-3xl font-semibold tracking-tight text-white">
            Previous searches
          </h1>
          <p className="mt-2 text-sm text-slate-500">
            Every search you run while signed in is saved here so you can replay it later.
          </p>
        </div>

        {authLoading || loading ? (
          <div className="flex justify-center py-20">
            <LoaderCircle className="h-7 w-7 animate-spin text-emerald-400" />
          </div>
        ) : !user ? (
          <div className="rounded-2xl border border-white/8 bg-white/[0.03] px-6 py-16 text-center">
            <p className="font-medium text-white">Sign in to keep search history</p>
            <p className="mt-2 text-sm text-slate-500">
              Signed-in searches are stored against your Google account.
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
            {error && (
              <p className="mb-4 rounded-lg border border-rose-400/20 bg-rose-500/10 px-3 py-2 text-xs text-rose-300">
                {error}
              </p>
            )}
            {searches.length === 0 ? (
              <div className="rounded-2xl border border-dashed border-white/10 px-6 py-16 text-center">
                <Search className="mx-auto h-8 w-8 text-slate-600" />
                <p className="mt-4 text-sm text-slate-400">
                  No saved searches yet. Run a search while signed in.
                </p>
                <Link
                  href="/search"
                  className="mt-4 inline-flex text-sm text-emerald-400 hover:text-emerald-300"
                >
                  Go to search →
                </Link>
              </div>
            ) : (
              <ul className="space-y-3">
                {searches.map((row) => (
                  <li
                    key={row.id}
                    className="rounded-2xl border border-white/8 bg-white/[0.03] p-4 sm:p-5"
                  >
                    <div className="flex flex-wrap items-start gap-4">
                      <div className="min-w-0 flex-1">
                        <p className="text-base font-semibold text-white">
                          {row.role}
                          {row.alternate_role ? (
                            <span className="font-normal text-slate-500">
                              {" "}
                              / {row.alternate_role}
                            </span>
                          ) : null}
                        </p>
                        <div className="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-xs text-slate-500">
                          {row.location_label && <span>{row.location_label}</span>}
                          {row.skills && (
                            <span className="truncate max-w-xs">{row.skills}</span>
                          )}
                          {row.company && <span>Company: {row.company}</span>}
                          <span className="inline-flex items-center gap-1">
                            <Clock3 className="h-3 w-3" />
                            {new Date(row.created_at).toLocaleString()}
                          </span>
                          <span>{row.result_count} results</span>
                        </div>
                        {row.experience_bands?.length > 0 && (
                          <div className="mt-2 flex flex-wrap gap-1.5">
                            {row.experience_bands.map((band) => (
                              <span
                                key={band}
                                className="rounded-md border border-white/8 px-2 py-0.5 text-[10px] text-slate-400"
                              >
                                {band} yrs
                              </span>
                            ))}
                          </div>
                        )}
                      </div>
                      <div className="flex gap-2">
                        {row.results_json && row.results_json.length > 0 && (
                          <Link
                            href={`/history/${row.id}`}
                            className="inline-flex items-center gap-1.5 rounded-lg border border-emerald-400/20 bg-emerald-500/10 px-3 py-2 text-xs font-semibold text-emerald-300 hover:bg-emerald-500/20"
                          >
                            View jobs
                          </Link>
                        )}
                        <button
                          type="button"
                          onClick={() => rerun(row)}
                          className="inline-flex items-center gap-1.5 rounded-lg bg-emerald-400 px-3 py-2 text-xs font-semibold text-[#07100c] hover:bg-emerald-300"
                        >
                          <RotateCcw className="h-3.5 w-3.5" />
                          Re-run
                        </button>
                        <button
                          type="button"
                          disabled={busyId === row.id}
                          onClick={() => remove(row.id)}
                          className="inline-flex items-center gap-1 rounded-lg border border-rose-400/20 px-2.5 py-2 text-xs text-rose-300 hover:bg-rose-500/10 disabled:opacity-50"
                        >
                          <Trash2 className="h-3.5 w-3.5" />
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
