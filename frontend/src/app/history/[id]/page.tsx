"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { JobSearchApp } from "@/components/job-search-app";
import { api } from "@/lib/api";
import { SavedSearch } from "@/types";
import { LoaderCircle } from "lucide-react";
import { AppShell } from "@/components/app-shell";

export default function HistoryDetailsPage() {
  const params = useParams();
  const router = useRouter();
  const id = params.id as string;

  const [historyItem, setHistoryItem] = useState<SavedSearch | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) {
      router.push("/history");
      return;
    }

    let mounted = true;
    api
      .getSearchHistoryById(id)
      .then((data) => {
        if (mounted) {
          setHistoryItem(data);
          setLoading(false);
        }
      })
      .catch((err) => {
        if (mounted) {
          setError(err.message || "Failed to load history");
          setLoading(false);
        }
      });

    return () => {
      mounted = false;
    };
  }, [id, router]);

  if (loading) {
    return (
      <AppShell>
        <div className="flex min-h-[50vh] items-center justify-center">
          <LoaderCircle className="h-8 w-8 animate-spin text-emerald-400" />
        </div>
      </AppShell>
    );
  }

  if (error || !historyItem) {
    return (
      <AppShell>
        <div className="mx-auto max-w-7xl px-4 py-12 sm:px-6">
          <div className="rounded-2xl border border-red-500/20 bg-red-500/10 p-6 text-center text-red-300">
            <h2 className="mb-2 text-lg font-semibold">Error</h2>
            <p>{error || "History not found."}</p>
            <button
              onClick={() => router.push("/history")}
              className="mt-4 rounded-lg bg-red-500/20 px-4 py-2 text-sm font-semibold hover:bg-red-500/30"
            >
              Back to History
            </button>
          </div>
        </div>
      </AppShell>
    );
  }

  return <JobSearchApp initialHistoryItem={historyItem} />;
}
