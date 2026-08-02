"use client";

import { Suspense } from "react";
import { LoaderCircle } from "lucide-react";

import { AppShell } from "@/components/app-shell";
import { JobSearchApp } from "@/components/job-search-app";

export default function SearchPage() {
  return (
    <Suspense
      fallback={
        <AppShell>
          <div className="flex justify-center py-24">
            <LoaderCircle className="h-7 w-7 animate-spin text-emerald-400" />
          </div>
        </AppShell>
      }
    >
      <JobSearchApp />
    </Suspense>
  );
}
