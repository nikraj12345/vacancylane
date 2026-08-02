"use client";

import { useMutation, useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { JobSearchRequest } from "@/types";

export function useAtsSources() {
  return useQuery({
    queryKey: ["ats-sources"],
    queryFn: api.getAtsSources,
  });
}

export function useSearchStatus() {
  return useQuery({
    queryKey: ["search-status"],
    queryFn: api.getSearchStatus,
    staleTime: 60_000,
  });
}

export function useJobSearch() {
  return useMutation({
    mutationFn: (data: JobSearchRequest) => api.searchJobs(data),
  });
}

export function useGoogleLinks() {
  return useMutation({
    mutationFn: (data: JobSearchRequest) => api.getGoogleLinks(data),
  });
}

export function useParseResume() {
  return useMutation({
    mutationFn: (file: File) => api.parseResume(file),
  });
}
