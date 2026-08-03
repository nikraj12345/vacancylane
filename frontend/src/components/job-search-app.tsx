"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { useSearchParams } from "next/navigation";
import {
  ArrowUpDown,
  BriefcaseBusiness,
  Building2,
  CalendarDays,
  Check,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  ExternalLink,
  FileUp,
  Filter,
  LoaderCircle,
  MapPin,
  Search,
  ShieldCheck,
  SlidersHorizontal,
  Sparkles,
  Target,
  Wifi,
} from "lucide-react";
import { AppShell } from "@/components/app-shell";
import { useAuth } from "@/components/auth-provider";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ExperienceMultiSelect } from "@/components/experience-multi-select";
import { LocationMultiSelect } from "@/components/location-multi-select";
import { api } from "@/lib/api";
import {
  useAtsSources,
  useGoogleLinks,
  useJobSearch,
  useParseResume,
  useSearchStatus,
} from "@/hooks/use-job-search";
import type { ExperienceBandId } from "@/lib/experience";
import {
  getSpecialLocations,
  locationLabels,
  locationsToFilters,
  locationsToQueryClause,
  resumeLocationsToOptions,
  type LocationOption,
} from "@/lib/locations";
import { searchSchema } from "@/lib/validators";
import { cn } from "@/lib/utils";
import type {
  GoogleLinksResponse,
  JobListing,
  JobSearchRequest,
  JobSearchResponse,
  SavedSearch,
} from "@/types";

const DEFAULT_SOURCES = [
  "greenhouse",
  "lever",
  "ashby",
  "workday",
  "smartrecruiters",
  "workable",
  "linkedin",
  "wellfound",
  "instahyre",
];

// Best to worst, mirroring the backend's MATCH_ORDER.
const LOCATION_ORDER = ["match", "remote", "country", "unknown", "mismatch"];

/** Location verdicts the "In my locations" filter keeps. */
const IN_MY_LOCATIONS = new Set(["match", "remote", "country"]);

function locationRank(verdict: string): number {
  const index = LOCATION_ORDER.indexOf(verdict);
  return index === -1 ? LOCATION_ORDER.length : index;
}

const DATE_OPTIONS = [
  ["day", "Past 24 hours"],
  ["week", "Past week"],
  ["month", "Past month"],
  ["year", "Past year"],
  ["any", "Any time"],
] as const;

const EMPLOYMENT_OPTIONS = [
  "",
  "Full-time",
  "Part-time",
  "Contract",
] as const;

export function JobSearchApp({
  initialHistoryItem,
}: {
  initialHistoryItem?: SavedSearch;
} = {}) {
  const { data: atsSources = [] } = useAtsSources();
  const { data: searchStatus } = useSearchStatus();
  const searchMutation = useJobSearch();
  const googleLinksMutation = useGoogleLinks();
  const resumeMutation = useParseResume();
  const resumeInputRef = useRef<HTMLInputElement>(null);
  const [resumeSummary, setResumeSummary] = useState<string | null>(null);

  const [role, setRole] = useState("AI Engineer");
  const [locations, setLocations] = useState<LocationOption[]>([
    getSpecialLocations()[0],
  ]);
  const [alternateRole, setAlternateRole] = useState("Machine Learning Engineer");
  const [skills, setSkills] = useState("Python, LLM, RAG");
  const [experienceBands, setExperienceBands] = useState<ExperienceBandId[]>([]);
  const [company, setCompany] = useState("");
  const [datePosted, setDatePosted] =
    useState<"any" | "day" | "week" | "month" | "year">("month");
  const [employmentType, setEmploymentType] =
    useState<"" | "Full-time" | "Part-time" | "Contract">("");
  const [remoteOnly, setRemoteOnly] = useState(false);
  const [verifyLive, setVerifyLive] = useState(true);
  const [rawResults, setRawResults] = useState(false);
  const [selectedSources, setSelectedSources] =
    useState<string[]>(DEFAULT_SOURCES);
  const [advancedOpen, setAdvancedOpen] = useState(false);
  const [results, setResults] = useState<JobSearchResponse | null>(null);
  const [googleLinks, setGoogleLinks] = useState<GoogleLinksResponse | null>(
    null
  );
  const [error, setError] = useState<string | null>(null);

  // Result-side filters do not trigger another web search.
  const [keyword, setKeyword] = useState("");
  const [resultSource, setResultSource] = useState("all");
  const [resultRemoteOnly, setResultRemoteOnly] = useState(false);
  // On by default: a posting the ATS will not confirm as open is the main
  // source of dead links, and the toggle is there to widen the net on demand.
  const [verifiedOnly, setVerifiedOnly] = useState(true);
  const [locationMatchOnly, setLocationMatchOnly] = useState(false);
  const [minRelevance, setMinRelevance] = useState(0);
  const [sort, setSort] = useState<"relevance" | "recent" | "title">(
    "relevance"
  );
  const [showQueries, setShowQueries] = useState(false);
  const { user } = useAuth();
  const searchParams = useSearchParams();
  const rerunApplied = useRef(false);

  const visibleJobs = useMemo(() => {
    if (!results) return [];
    const needle = keyword.trim().toLowerCase();
    const filtered = results.jobs.filter((job) => {
      const text = `${job.title} ${job.company || ""} ${job.snippet}`.toLowerCase();
      return (
        (!needle || text.includes(needle)) &&
        (resultSource === "all" || job.source === resultSource) &&
        (!resultRemoteOnly || job.is_remote) &&
        (!verifiedOnly || job.verified) &&
        (!locationMatchOnly || IN_MY_LOCATIONS.has(job.location_match)) &&
        job.relevance_score >= minRelevance
      );
    });
    return [...filtered].sort((a, b) => {
      if (sort === "title") return a.title.localeCompare(b.title);
      if (sort === "recent") {
        return (b.posted_at || "").localeCompare(a.posted_at || "");
      }
      // Jobs in the requested locations come first, then the same country,
      // then unplaced ones; relevance orders each group.
      const byLocation = locationRank(a.location_match) - locationRank(b.location_match);
      if (byLocation !== 0) return byLocation;
      return b.relevance_score - a.relevance_score;
    });
  }, [
    results,
    keyword,
    resultSource,
    resultRemoteOnly,
    verifiedOnly,
    locationMatchOnly,
    minRelevance,
    sort,
  ]);

  const resultSources = useMemo(() => {
    if (!results) return [];
    return [...new Set(results.jobs.map((job) => job.source))];
  }, [results]);

  useEffect(() => {
    if (rerunApplied.current) return;
    if (initialHistoryItem) {
      rerunApplied.current = true;
      try {
        const payload = initialHistoryItem.payload as unknown as JobSearchRequest;
        const savedResults = {
          jobs: initialHistoryItem.results_json || [],
          total: initialHistoryItem.result_count || 0,
          queries_used: [],
          search_providers: [],
          raw_results: payload.raw_results || false,
          google_enabled: false,
          query_count: 0,
          removed_closed: 0,
          variables: {},
        } as JobSearchResponse;
        setResults(savedResults);
        if (payload.role) setRole(payload.role);
        if (payload.alternate_role) setAlternateRole(payload.alternate_role);
        if (typeof payload.skills === "string") {
          setSkills(payload.skills.replaceAll(" OR ", ", "));
        }
        if (payload.company) setCompany(payload.company);
        if (payload.experience_bands?.length) {
          setExperienceBands(payload.experience_bands as ExperienceBandId[]);
        }
        if (payload.sources?.length) setSelectedSources(payload.sources);
        if (payload.date_posted) setDatePosted(payload.date_posted);
        if (payload.employment_type !== undefined) {
          setEmploymentType(payload.employment_type);
        }
        if (payload.locations?.length) {
          setLocations(
            resumeLocationsToOptions(
              payload.locations.map((loc) => ({
                label: loc.label,
                city: loc.city,
                country: loc.country,
                remote: loc.remote,
              }))
            )
          );
        }
      } catch {
        // ignore
      }
    } else if (searchParams.get("rerun") === "1") {
      rerunApplied.current = true;
      try {
      const raw = sessionStorage.getItem("vacancylane_rerun");
      if (!raw) return;
      sessionStorage.removeItem("vacancylane_rerun");
      const payload = JSON.parse(raw) as JobSearchRequest;
      if (payload.role) setRole(payload.role);
      if (payload.alternate_role) setAlternateRole(payload.alternate_role);
      if (typeof payload.skills === "string") {
        setSkills(payload.skills.replaceAll(" OR ", ", "));
      }
      if (payload.company) setCompany(payload.company);
      if (payload.experience_bands?.length) {
        setExperienceBands(payload.experience_bands as ExperienceBandId[]);
      }
      if (payload.sources?.length) setSelectedSources(payload.sources);
      if (payload.date_posted) setDatePosted(payload.date_posted);
      if (payload.employment_type !== undefined) {
        setEmploymentType(payload.employment_type);
      }
      if (payload.locations?.length) {
        setLocations(
          resumeLocationsToOptions(
            payload.locations.map((loc) => ({
              label: loc.label,
              city: loc.city,
              country: loc.country,
              remote: loc.remote,
            }))
          )
        );
      }
    } catch {
      // ignore malformed rerun payload
    }
    } else {
      rerunApplied.current = true;
      try {
        const rawResults = sessionStorage.getItem("vacancylane_current_results");
        const rawParams = sessionStorage.getItem("vacancylane_search_params");
        if (rawResults && rawParams) {
          const payload = JSON.parse(rawParams) as JobSearchRequest;
          const savedResults = JSON.parse(rawResults) as JobSearchResponse;
          setResults(savedResults);
          if (payload.role) setRole(payload.role);
          if (payload.alternate_role) setAlternateRole(payload.alternate_role);
          if (typeof payload.skills === "string") {
            setSkills(payload.skills.replaceAll(" OR ", ", "));
          }
          if (payload.company) setCompany(payload.company);
          if (payload.experience_bands?.length) {
            setExperienceBands(payload.experience_bands as ExperienceBandId[]);
          }
          if (payload.sources?.length) setSelectedSources(payload.sources);
          if (payload.date_posted) setDatePosted(payload.date_posted);
          if (payload.employment_type !== undefined) {
            setEmploymentType(payload.employment_type);
          }
          if (payload.locations?.length) {
            setLocations(
              resumeLocationsToOptions(
                payload.locations.map((loc) => ({
                  label: loc.label,
                  city: loc.city,
                  country: loc.country,
                  remote: loc.remote,
                }))
              )
            );
          }
        }
      } catch {
        // ignore
      }
    }
  }, [searchParams, initialHistoryItem]);

  function toggleSource(slug: string) {
    setSelectedSources((current) =>
      current.includes(slug)
        ? current.filter((source) => source !== slug)
        : [...current, slug]
    );
  }

  function buildSearchPayload(): JobSearchRequest | null {
    const locationClause = locationsToQueryClause(locations);
    const hasRemote = locations.some(
      (item) => item.label.toLowerCase() === "remote"
    );
    const parsed = searchSchema.safeParse({
      role,
      location: locationClause,
      locations: locationsToFilters(locations),
      alternate_role: alternateRole,
      skills: skills.replaceAll(",", " OR "),
      experience: "",
      experience_bands: experienceBands,
      company,
      sources: selectedSources,
      date_posted: datePosted,
      remote_only: remoteOnly || (hasRemote && locations.length === 1),
      employment_type: employmentType,
      verify_live: verifyLive,
      raw_results: rawResults,
    });
    if (!parsed.success) {
      setError(parsed.error.issues[0]?.message || "Check your filters");
      return null;
    }
    return parsed.data;
  }

  async function runSearch(event: React.FormEvent) {
    event.preventDefault();
    const payload = buildSearchPayload();
    if (!payload) return;

    setError(null);
    setKeyword("");
    setResultSource("all");
    setResultRemoteOnly(false);
    // Raw mode never verifies, so leaving this on would hide every result.
    setVerifiedOnly(!rawResults && verifyLive);
    setLocationMatchOnly(false);
    setMinRelevance(0);
    try {
      const data = await searchMutation.mutateAsync(payload);
      setResults(data);
      try {
        sessionStorage.setItem("vacancylane_current_results", JSON.stringify(data));
        sessionStorage.setItem("vacancylane_search_params", JSON.stringify(payload));
      } catch {
        // ignore
      }
      // Backend also persists history when the bearer token is present; this
      // client save is a backup and refreshes the History page sooner.
      if (user) {
        try {
          await api.saveSearch({
            role: payload.role,
            alternate_role: payload.alternate_role || null,
            location_label: locationLabels(locations) || null,
            skills: skills || null,
            company: payload.company || null,
            experience_bands: payload.experience_bands || [],
            sources: payload.sources || [],
            payload,
            result_count: data.total,
            results_json: data.jobs,
          });
        } catch (historyError) {
          const message =
            historyError instanceof Error
              ? historyError.message
              : "Could not save this search to history";
          // Don't fail the search UI — surface a soft warning instead.
          setError(message);
        }
      }
    } catch (searchError) {
      setError(
        searchError instanceof Error ? searchError.message : "Search failed"
      );
    }
  }

  async function openOnGoogle() {
    const payload = buildSearchPayload();
    if (!payload) return;

    setError(null);
    // Open the tab during the click handler so popup blockers allow it.
    const popup = window.open("about:blank", "_blank");
    try {
      const links = await googleLinksMutation.mutateAsync(payload);
      setGoogleLinks(links);
      setShowQueries(true);
      if (popup) {
        popup.opener = null;
        popup.location.href = links.combined_google_url;
      } else {
        window.location.assign(links.combined_google_url);
      }
    } catch (googleError) {
      popup?.close();
      setError(
        googleError instanceof Error
          ? googleError.message
          : "Could not build Google links"
      );
    }
  }

  async function onResumeSelected(event: React.ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    event.target.value = "";
    if (!file) return;

    setError(null);
    try {
      const profile = await resumeMutation.mutateAsync(file);
      if (profile.role) setRole(profile.role);
      if (profile.alternate_role) setAlternateRole(profile.alternate_role);
      if (profile.skills_text) setSkills(profile.skills_text);
      if (profile.experience_bands.length) {
        setExperienceBands(profile.experience_bands as ExperienceBandId[]);
      }
      const fromResume = resumeLocationsToOptions(profile.locations);
      if (fromResume.length) setLocations(fromResume);
      setResumeSummary(profile.summary || file.name);
      setAdvancedOpen(true);
      if (profile.warnings.length) {
        setError(profile.warnings.join(" "));
      }
    } catch (resumeError) {
      setResumeSummary(null);
      setError(
        resumeError instanceof Error
          ? resumeError.message
          : "Could not read that resume"
      );
    }
  }

  return (
    <AppShell>
      <main className="relative mx-auto max-w-7xl px-4 py-8 sm:px-6">
        <section className="mb-7">
          <div className="mb-5 flex flex-wrap items-end justify-between gap-4">
            <div>
              <div className="mb-2 flex items-center gap-2 text-sm font-medium text-emerald-300">
                <Sparkles className="h-4 w-4" />
                Precision job search
              </div>
              <h2 className="max-w-3xl font-[family-name:var(--font-display)] text-3xl font-semibold tracking-tight text-white sm:text-4xl">
                Find jobs directly from company hiring systems.
              </h2>
              <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-400">
                Results are validated, ranked by location fit, and ready to track
                when you apply.
              </p>
            </div>
            <div className="flex flex-wrap items-center gap-3">
              <input
                ref={resumeInputRef}
                type="file"
                accept=".pdf,.docx,.txt,.md,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document,text/plain"
                className="hidden"
                onChange={onResumeSelected}
              />
              <Button
                type="button"
                variant="outline"
                disabled={resumeMutation.isPending}
                onClick={() => resumeInputRef.current?.click()}
                className="h-10 rounded-xl border-white/10 bg-white/[0.04] px-4 text-sm font-medium text-slate-200 hover:bg-white/5 hover:text-white"
              >
                {resumeMutation.isPending ? (
                  <LoaderCircle className="h-4 w-4 animate-spin" />
                ) : (
                  <FileUp className="h-4 w-4" />
                )}
                {resumeMutation.isPending
                  ? "Reading resume..."
                  : "Search from resume"}
              </Button>
              {resumeSummary && (
                <span className="max-w-xl truncate text-xs text-slate-400">
                  Filled from resume · {resumeSummary}
                </span>
              )}
            </div>
          </div>

          <form
            onSubmit={runSearch}
            className="overflow-hidden rounded-2xl border border-white/10 bg-white/[0.045] shadow-2xl shadow-black/20 backdrop-blur"
          >
            <div className="grid gap-px bg-white/8 lg:grid-cols-[1fr_1.35fr_auto]">
              <SearchField
                icon={<BriefcaseBusiness className="h-4 w-4" />}
                label="Job title"
              >
                <input
                  value={role}
                  onChange={(event) => setRole(event.target.value)}
                  placeholder="e.g. Backend Engineer"
                  className="w-full bg-transparent text-sm text-white outline-none placeholder:text-slate-600"
                />
              </SearchField>
              <div className="flex min-h-20 flex-col justify-center bg-[#111513] px-4 py-3">
                <span className="mb-1.5 flex items-center gap-2 text-[10px] font-bold uppercase tracking-[.16em] text-slate-500">
                  <MapPin className="h-3.5 w-3.5 text-emerald-400" />
                  Locations
                  {locations.length > 0 && (
                    <span className="rounded bg-emerald-400/10 px-1.5 py-0.5 text-[9px] text-emerald-300">
                      {locations.length} selected
                    </span>
                  )}
                </span>
                <LocationMultiSelect
                  value={locations}
                  onChange={setLocations}
                  placeholder="Select cities or countries..."
                />
              </div>
              <div className="flex flex-col gap-2 bg-[#111513] p-3 sm:flex-row sm:items-center">
                <Button
                  type="submit"
                  disabled={searchMutation.isPending}
                  className="h-12 w-full rounded-xl bg-emerald-400 px-7 text-sm font-semibold text-[#07100c] shadow-lg shadow-emerald-950/40 hover:bg-emerald-300 lg:w-auto"
                >
                  {searchMutation.isPending ? (
                    <LoaderCircle className="h-4 w-4 animate-spin" />
                  ) : (
                    <Search className="h-4 w-4" />
                  )}
                  {searchMutation.isPending ? "Searching..." : "Search jobs"}
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  disabled={googleLinksMutation.isPending}
                  onClick={openOnGoogle}
                  className="h-12 w-full rounded-xl border-white/10 bg-black/20 px-5 text-sm font-semibold text-slate-200 hover:bg-white/5 hover:text-white lg:w-auto"
                >
                  {googleLinksMutation.isPending ? (
                    <LoaderCircle className="h-4 w-4 animate-spin" />
                  ) : (
                    <ExternalLink className="h-4 w-4" />
                  )}
                  Open on Google
                </Button>
              </div>
            </div>

            <div className="border-t border-white/8 p-4">
              <div className="flex flex-wrap items-center gap-2">
                <ExperienceMultiSelect
                  value={experienceBands}
                  onChange={setExperienceBands}
                />
                <Select
                  value={datePosted}
                  onChange={(value) =>
                    setDatePosted(
                      value as "any" | "day" | "week" | "month" | "year"
                    )
                  }
                  ariaLabel="Date posted"
                >
                  {DATE_OPTIONS.map(([value, label]) => (
                    <option key={value} value={value}>
                      {label}
                    </option>
                  ))}
                </Select>
                <Select
                  value={employmentType}
                  onChange={(value) =>
                    setEmploymentType(
                      value as "" | "Full-time" | "Part-time" | "Contract"
                    )
                  }
                  ariaLabel="Employment type"
                >
                  {EMPLOYMENT_OPTIONS.map((value) => (
                    <option key={value || "all"} value={value}>
                      {value || "Any job type"}
                    </option>
                  ))}
                </Select>
                <Toggle
                  active={remoteOnly}
                  onClick={() => setRemoteOnly((value) => !value)}
                  icon={<Wifi className="h-3.5 w-3.5" />}
                  label="Remote only"
                />
                <Toggle
                  active={verifyLive && !rawResults}
                  onClick={() => setVerifyLive((value) => !value)}
                  icon={<ShieldCheck className="h-3.5 w-3.5" />}
                  label="Hide closed jobs"
                  title={
                    rawResults
                      ? "Disabled while Raw results is on"
                      : "Opens every result to drop postings that are already filled or removed"
                  }
                />
                <Toggle
                  active={rawResults}
                  onClick={() => setRawResults((value) => !value)}
                  icon={<Sparkles className="h-3.5 w-3.5" />}
                  label="Raw results"
                  title="Show every search hit with no filtering: no closed-posting check, no location, experience or relevance filter"
                />
                <button
                  type="button"
                  onClick={() => setAdvancedOpen((value) => !value)}
                  className="ml-auto inline-flex h-9 items-center gap-2 rounded-lg px-3 text-xs font-medium text-slate-400 hover:bg-white/5 hover:text-white"
                >
                  <SlidersHorizontal className="h-3.5 w-3.5" />
                  Advanced filters
                  {advancedOpen ? (
                    <ChevronUp className="h-3.5 w-3.5" />
                  ) : (
                    <ChevronDown className="h-3.5 w-3.5" />
                  )}
                </button>
              </div>

              {advancedOpen && (
                <div className="mt-4 border-t border-white/8 pt-4">
                  <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
                    <Field label="Alternate title">
                      <Input
                        value={alternateRole}
                        onChange={(event) => setAlternateRole(event.target.value)}
                        placeholder="ML Engineer"
                        className="h-10 border-white/10 bg-black/20"
                      />
                    </Field>
                    <Field label="Skills">
                      <Input
                        value={skills}
                        onChange={(event) => setSkills(event.target.value)}
                        placeholder="Python, FastAPI, AWS"
                        className="h-10 border-white/10 bg-black/20"
                      />
                    </Field>
                    <Field label="Company">
                      <Input
                        value={company}
                        onChange={(event) => setCompany(event.target.value)}
                        placeholder="Stripe, OpenAI..."
                        className="h-10 border-white/10 bg-black/20"
                      />
                    </Field>
                  </div>
                  {locations.length > 0 && (
                    <p className="mt-3 text-[11px] text-slate-500">
                      Searching in: {locationLabels(locations)}
                    </p>
                  )}

                  <div className="mt-4">
                    <div className="mb-2 flex items-center justify-between">
                      <span className="text-[10px] font-semibold uppercase tracking-[.16em] text-slate-500">
                        Search sources
                      </span>
                      <button
                        type="button"
                        onClick={() =>
                          setSelectedSources(
                            selectedSources.length
                              ? []
                              : atsSources.map((source) => source.slug)
                          )
                        }
                        className="text-[11px] text-emerald-400 hover:text-emerald-300"
                      >
                        {selectedSources.length ? "Clear all" : "Select all"}
                      </button>
                    </div>
                    <div className="flex flex-wrap gap-2">
                      {(atsSources.length
                        ? atsSources
                        : DEFAULT_SOURCES.map((slug) => ({
                            slug,
                            name: slug,
                          }))
                      ).map((source) => (
                        <button
                          key={source.slug}
                          type="button"
                          onClick={() => toggleSource(source.slug)}
                          className={cn(
                            "inline-flex h-8 items-center gap-1.5 rounded-lg border px-2.5 text-xs transition",
                            selectedSources.includes(source.slug)
                              ? "border-emerald-400/30 bg-emerald-400/10 text-emerald-200"
                              : "border-white/8 bg-black/10 text-slate-500 hover:border-white/15"
                          )}
                        >
                          {selectedSources.includes(source.slug) && (
                            <Check className="h-3 w-3" />
                          )}
                          {source.name}
                        </button>
                      ))}
                    </div>
                  </div>
                </div>
              )}

              {error && (
                <div className="mt-3 rounded-lg border border-red-400/20 bg-red-500/10 px-3 py-2 text-xs text-red-300">
                  {error}
                </div>
              )}
            </div>
          </form>

          {googleLinks && (
            <div className="mt-4 rounded-2xl border border-white/10 bg-white/[0.035] p-4">
              <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
                <div>
                  <p className="text-sm font-semibold text-white">
                    Google search links
                  </p>
                  <p className="mt-1 text-xs text-slate-500">
                    Results open on google.com. Use these when you want Google
                    ranking for the same ATS dorks.
                  </p>
                </div>
                <a
                  href={googleLinks.combined_google_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex h-9 items-center gap-2 rounded-lg bg-emerald-400 px-3 text-xs font-semibold text-[#07100c] hover:bg-emerald-300"
                >
                  Open combined search
                  <ExternalLink className="h-3.5 w-3.5" />
                </a>
              </div>
              <div className="mb-3 rounded-lg border border-white/8 bg-black/20 p-3">
                <p className="mb-1 text-[10px] font-bold uppercase tracking-widest text-slate-500">
                  Combined query
                </p>
                <code className="block break-all text-[11px] leading-5 text-slate-400">
                  {googleLinks.combined_query}
                </code>
              </div>
              <div className="grid gap-2 sm:grid-cols-2">
                {googleLinks.links.map((link) => (
                  <a
                    key={link.source}
                    href={link.google_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="rounded-xl border border-white/8 bg-black/15 p-3 transition hover:border-emerald-400/25 hover:bg-emerald-400/[0.06]"
                  >
                    <div className="mb-1 flex items-center justify-between gap-2">
                      <span className="text-sm font-medium text-slate-200">
                        {link.source_name}
                      </span>
                      <ExternalLink className="h-3.5 w-3.5 text-slate-500" />
                    </div>
                    <code className="block break-all text-[11px] leading-5 text-slate-500">
                      {link.query}
                    </code>
                  </a>
                ))}
              </div>
            </div>
          )}
        </section>

        {searchMutation.isPending && (
          <SearchingState googleEnabled={searchStatus?.google_enabled} />
        )}

        {!results && !searchMutation.isPending && <EmptyState />}

        {results && !searchMutation.isPending && (
          <section className="grid gap-5 lg:grid-cols-[220px_minmax(0,1fr)]">
            <ResultFilters
              results={results}
              sources={resultSources}
              keyword={keyword}
              setKeyword={setKeyword}
              source={resultSource}
              setSource={setResultSource}
              remoteOnly={resultRemoteOnly}
              setRemoteOnly={setResultRemoteOnly}
              verifiedOnly={verifiedOnly}
              setVerifiedOnly={setVerifiedOnly}
              locationMatchOnly={locationMatchOnly}
              setLocationMatchOnly={setLocationMatchOnly}
              minRelevance={minRelevance}
              setMinRelevance={setMinRelevance}
            />

            <div className="min-w-0">
              <div className="mb-4 flex flex-wrap items-end justify-between gap-3">
                <div>
                  <p className="text-xl font-semibold text-white">
                    {visibleJobs.length} matching jobs
                  </p>
                  <p className="mt-1 text-xs text-slate-500">
                    {results.total} live links ·{" "}
                    {results.query_count || results.queries_used.length} query
                    permutations across{" "}
                    {new Set(results.queries_used.map((q) => q.source)).size}{" "}
                    ATS sources
                  </p>
                  <div className="mt-1.5 flex flex-wrap gap-1.5">
                    {results.raw_results && (
                      <span className="inline-flex items-center gap-1.5 rounded-md border border-fuchsia-400/20 bg-fuchsia-500/10 px-2 py-1 text-[11px] text-fuchsia-300">
                        <Sparkles className="h-3.5 w-3.5" />
                        Raw mode · no filtering applied
                      </span>
                    )}
                    {results.google_enabled && (
                      <span className="inline-flex items-center gap-1.5 rounded-md border border-emerald-400/20 bg-emerald-400/8 px-2 py-1 text-[11px] text-emerald-300">
                        <Sparkles className="h-3.5 w-3.5" />
                        Google results
                        {(() => {
                          const labels = (results.search_providers || [])
                            .filter((p) => p.startsWith("google:"))
                            .map((p) => p.replace("google:", ""));
                          return labels.length ? ` · ${labels.join(", ")}` : "";
                        })()}
                      </span>
                    )}
                    {results.removed_closed > 0 && (
                      <span className="inline-flex items-center gap-1.5 rounded-md border border-emerald-400/20 bg-emerald-500/10 px-2 py-1 text-[11px] text-emerald-300">
                        <ShieldCheck className="h-3.5 w-3.5" />
                        {results.removed_closed} closed{" "}
                        {results.removed_closed === 1 ? "posting" : "postings"}{" "}
                        removed
                      </span>
                    )}
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={() => setShowQueries((value) => !value)}
                    className="h-9 rounded-lg border border-white/8 bg-white/[0.03] px-3 text-xs text-slate-400 hover:text-white"
                  >
                    {showQueries ? "Hide" : "View"} search logic
                  </button>
                  <div className="relative">
                    <ArrowUpDown className="pointer-events-none absolute left-3 top-2.5 h-3.5 w-3.5 text-slate-500" />
                    <select
                      value={sort}
                      onChange={(event) =>
                        setSort(
                          event.target.value as
                            | "relevance"
                            | "recent"
                            | "title"
                        )
                      }
                      className="h-9 appearance-none rounded-lg border border-white/8 bg-[#101411] pl-8 pr-8 text-xs text-slate-300 outline-none"
                    >
                      <option value="relevance">Most relevant</option>
                      <option value="recent">Most recent</option>
                      <option value="title">Title A–Z</option>
                    </select>
                  </div>
                </div>
              </div>

              {showQueries && results && (
                <div className="mb-4 max-h-64 space-y-3 overflow-y-auto rounded-xl border border-emerald-400/15 bg-emerald-400/[0.04] p-4">
                  {results.queries_used.map((query, index) => (
                    <div key={`${query.source}-${query.label}-${index}`}>
                      <div className="mb-1 flex items-center justify-between gap-2">
                        <p className="text-[10px] font-bold uppercase tracking-widest text-emerald-300">
                          {query.source_name}
                          {query.label ? ` · ${query.label}` : ""}
                        </p>
                        <a
                          href={`https://www.google.com/search?q=${encodeURIComponent(query.query)}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center gap-1 text-[10px] text-slate-500 hover:text-emerald-300"
                        >
                          Google
                          <ExternalLink className="h-3 w-3" />
                        </a>
                      </div>
                      <code className="block break-all text-[11px] leading-5 text-slate-500">
                        {query.query}
                      </code>
                    </div>
                  ))}
                </div>
              )}

              {visibleJobs.length ? (
                <div className="space-y-3">
                  {visibleJobs.map((job) => (
                    <JobCard key={job.url} job={job} />
                  ))}
                </div>
              ) : (
                <div className="rounded-xl border border-dashed border-white/10 p-12 text-center">
                  <Filter className="mx-auto mb-3 h-7 w-7 text-slate-600" />
                  <p className="text-sm font-medium text-slate-300">
                    No jobs match these result filters
                  </p>
                  <p className="mt-1 text-xs text-slate-500">
                    {verifiedOnly
                      ? "Confirmed live is on, so postings whose board publishes no status are hidden. Turn it off to see them."
                      : "Clear a filter or lower the relevance threshold."}
                  </p>
                </div>
              )}
            </div>
          </section>
        )}
      </main>
    </AppShell>
  );
}

function SearchField({
  icon,
  label,
  children,
}: {
  icon: React.ReactNode;
  label: string;
  children: React.ReactNode;
}) {
  return (
    <label className="flex min-h-20 items-center gap-3 bg-[#111513] px-5 py-3">
      <span className="text-emerald-400">{icon}</span>
      <span className="min-w-0 flex-1">
        <span className="mb-1 block text-[10px] font-bold uppercase tracking-[.16em] text-slate-500">
          {label}
        </span>
        {children}
      </span>
    </label>
  );
}

function Field({
  label,
  children,
}: {
  label: string;
  children: React.ReactNode;
}) {
  return (
    <label>
      <span className="mb-1.5 block text-[10px] font-semibold uppercase tracking-[.14em] text-slate-500">
        {label}
      </span>
      {children}
    </label>
  );
}

function Select({
  value,
  onChange,
  ariaLabel,
  children,
}: {
  value: string;
  onChange: (value: string) => void;
  ariaLabel: string;
  children: React.ReactNode;
}) {
  return (
    <select
      value={value}
      onChange={(event) => onChange(event.target.value)}
      aria-label={ariaLabel}
      className="h-9 rounded-lg border border-white/8 bg-[#101411] px-3 text-xs text-slate-300 outline-none hover:border-white/15 focus:border-emerald-400/50"
    >
      {children}
    </select>
  );
}

function Toggle({
  active,
  onClick,
  icon,
  label,
  title,
}: {
  active: boolean;
  onClick: () => void;
  icon: React.ReactNode;
  label: string;
  title?: string;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      title={title}
      className={cn(
        "inline-flex h-9 items-center gap-2 rounded-lg border px-3 text-xs transition",
        active
          ? "border-emerald-400/30 bg-emerald-400/10 text-emerald-200"
          : "border-white/8 bg-[#101411] text-slate-400 hover:border-white/15"
      )}
    >
      {icon}
      {label}
    </button>
  );
}

function ResultFilters({
  results,
  sources,
  keyword,
  setKeyword,
  source,
  setSource,
  remoteOnly,
  setRemoteOnly,
  verifiedOnly,
  setVerifiedOnly,
  locationMatchOnly,
  setLocationMatchOnly,
  minRelevance,
  setMinRelevance,
}: {
  results: JobSearchResponse;
  sources: string[];
  keyword: string;
  setKeyword: (value: string) => void;
  source: string;
  setSource: (value: string) => void;
  remoteOnly: boolean;
  setRemoteOnly: (value: boolean) => void;
  verifiedOnly: boolean;
  setVerifiedOnly: (value: boolean) => void;
  locationMatchOnly: boolean;
  setLocationMatchOnly: (value: boolean) => void;
  minRelevance: number;
  setMinRelevance: (value: number) => void;
}) {
  const verifiedCount = results.jobs.filter((job) => job.verified).length;
  const inLocationCount = results.jobs.filter((job) =>
    IN_MY_LOCATIONS.has(job.location_match)
  ).length;
  return (
    <aside className="h-fit rounded-xl border border-white/8 bg-white/[0.035] p-4 lg:sticky lg:top-5">
      <div className="mb-4 flex items-center gap-2 text-sm font-semibold text-white">
        <Filter className="h-4 w-4 text-emerald-400" />
        Refine results
      </div>
      <Field label="Search in results">
        <div className="relative">
          <Search className="absolute left-2.5 top-2.5 h-3.5 w-3.5 text-slate-600" />
          <Input
            value={keyword}
            onChange={(event) => setKeyword(event.target.value)}
            placeholder="Title, company, skill"
            className="h-9 border-white/8 bg-black/20 pl-8 text-xs"
          />
        </div>
      </Field>

      <div className="mt-5">
        <p className="mb-2 text-[10px] font-semibold uppercase tracking-[.14em] text-slate-500">
          Source
        </p>
        <div className="space-y-1">
          <SourceRadio
            active={source === "all"}
            label="All sources"
            count={results.jobs.length}
            onClick={() => setSource("all")}
          />
          {sources.map((slug) => {
            const jobs = results.jobs.filter((job) => job.source === slug);
            return (
              <SourceRadio
                key={slug}
                active={source === slug}
                label={jobs[0]?.source_name || slug}
                count={jobs.length}
                onClick={() => setSource(slug)}
              />
            );
          })}
        </div>
      </div>

      <div className="mt-5 flex flex-wrap gap-2">
        <Toggle
          active={remoteOnly}
          onClick={() => setRemoteOnly(!remoteOnly)}
          icon={<Wifi className="h-3.5 w-3.5" />}
          label="Remote results"
        />
        <Toggle
          active={verifiedOnly}
          onClick={() => setVerifiedOnly(!verifiedOnly)}
          icon={<ShieldCheck className="h-3.5 w-3.5" />}
          label={`Confirmed live (${verifiedCount})`}
          title="Only postings confirmed open through the ATS itself. Boards that publish no status stay out of this count."
        />
        <Toggle
          active={locationMatchOnly}
          onClick={() => setLocationMatchOnly(!locationMatchOnly)}
          icon={<MapPin className="h-3.5 w-3.5" />}
          label={`In my locations (${inLocationCount})`}
          title="Only postings whose published location matches your selection"
        />
      </div>

      <div className="mt-5">
        <div className="mb-2 flex justify-between text-[10px] font-semibold uppercase tracking-[.14em] text-slate-500">
          <span>Minimum match</span>
          <span className="text-emerald-300">{minRelevance}%</span>
        </div>
        <input
          type="range"
          min="0"
          max="90"
          step="10"
          value={minRelevance}
          onChange={(event) => setMinRelevance(Number(event.target.value))}
          className="w-full accent-emerald-400"
        />
      </div>
    </aside>
  );
}

function SourceRadio({
  active,
  label,
  count,
  onClick,
}: {
  active: boolean;
  label: string;
  count: number;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        "flex w-full items-center rounded-lg px-2.5 py-2 text-left text-xs transition",
        active
          ? "bg-emerald-400/8 text-emerald-200"
          : "text-slate-400 hover:bg-white/5"
      )}
    >
      <span
        className={cn(
          "mr-2 h-2 w-2 rounded-full border",
          active ? "border-emerald-400 bg-emerald-400" : "border-slate-600"
        )}
      />
      <span className="flex-1">{label}</span>
      <span className="text-[10px] text-slate-600">{count}</span>
    </button>
  );
}

function JobCard({ job }: { job: JobListing }) {
  const { user, appliedUrls, markApplied } = useAuth();
  const [applying, setApplying] = useState(false);
  const [applyError, setApplyError] = useState<string | null>(null);
  const alreadyApplied = appliedUrls.has(job.url);
  const companyInitial = (job.company || job.source_name).charAt(0).toUpperCase();

  async function onApply() {
    if (!user) {
      setApplyError("Sign in with Google to track applications");
      return;
    }
    setApplying(true);
    setApplyError(null);
    try {
      const row = await api.applyToJob({
        job_url: job.url,
        job_title: job.title,
        company: job.company,
        location: job.location,
        source: job.source,
        source_name: job.source_name,
      });
      markApplied(row);
      window.open(job.url, "_blank", "noopener,noreferrer");
    } catch (err) {
      setApplyError(err instanceof Error ? err.message : "Could not save application");
    } finally {
      setApplying(false);
    }
  }

  return (
    <article className="group rounded-2xl border border-white/8 bg-[#101310] p-4 transition duration-200 hover:-translate-y-0.5 hover:border-emerald-400/20 hover:bg-[#131714] sm:p-5">
      <div className="flex items-start gap-4">
        <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl border border-white/10 bg-gradient-to-br from-slate-800 to-slate-900 text-sm font-bold text-slate-300">
          {companyInitial}
        </div>
        <div className="min-w-0 flex-1">
          <div className="flex items-start gap-3">
            <div className="min-w-0 flex-1">
              <a
                href={job.url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-[15px] font-semibold leading-6 text-slate-100 transition group-hover:text-emerald-300"
              >
                {job.title}
              </a>
              <div className="mt-1 flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-slate-500">
                {job.company && (
                  <span className="inline-flex items-center gap-1.5 text-slate-400">
                    <Building2 className="h-3.5 w-3.5" />
                    {job.company}
                  </span>
                )}
                {job.location ? (
                  <span
                    title={
                      job.location_match === "country"
                        ? "Same country as your selection, different city"
                        : undefined
                    }
                    className={cn(
                      "inline-flex items-center gap-1.5",
                      (job.location_match === "match" ||
                        job.location_match === "remote") &&
                        "text-emerald-300/90",
                      job.location_match === "country" && "text-amber-300/80"
                    )}
                  >
                    <MapPin className="h-3.5 w-3.5" />
                    {job.location}
                  </span>
                ) : (
                  <span
                    title="This board does not publish a location for the posting"
                    className="inline-flex items-center gap-1.5 text-slate-600"
                  >
                    <MapPin className="h-3.5 w-3.5" />
                    Location not listed
                  </span>
                )}
                {job.posted_text && (
                  <span className="inline-flex items-center gap-1.5">
                    <CalendarDays className="h-3.5 w-3.5" />
                    {job.posted_text}
                  </span>
                )}
              </div>
            </div>
            <div
              title={`${job.relevance_score}% relevance`}
              className={cn(
                "inline-flex shrink-0 items-center gap-1 rounded-full border px-2 py-1 text-[10px] font-semibold",
                job.relevance_score >= 75
                  ? "border-emerald-400/20 bg-emerald-500/10 text-emerald-300"
                  : "border-emerald-400/20 bg-emerald-400/8 text-emerald-300"
              )}
            >
              <Target className="h-3 w-3" />
              {job.relevance_score}% match
            </div>
          </div>

          {job.snippet && (
            <p className="mt-3 line-clamp-2 text-xs leading-5 text-slate-500">
              {job.snippet}
            </p>
          )}

          <div className="mt-4 flex flex-wrap items-center gap-2">
            <span className="rounded-md border border-white/8 bg-black/20 px-2 py-1 text-[10px] font-medium text-slate-400">
              {job.source_name}
            </span>
            {job.verified && (
              <span
                title="Confirmed still open on the company's job board"
                className="inline-flex items-center gap-1 rounded-md border border-emerald-400/20 bg-emerald-500/10 px-2 py-1 text-[10px] font-medium text-emerald-300"
              >
                <ShieldCheck className="h-3 w-3" />
                Live
              </span>
            )}
            {job.is_remote && (
              <span className="rounded-md border border-violet-400/15 bg-violet-500/10 px-2 py-1 text-[10px] text-violet-300">
                Remote
              </span>
            )}
            {job.employment_type && (
              <span className="rounded-md border border-white/8 px-2 py-1 text-[10px] text-slate-400">
                {job.employment_type}
              </span>
            )}
            {/* {job.experience_years && (
              <span className="rounded-md border border-amber-400/20 bg-amber-500/10 px-2 py-1 text-[10px] text-amber-300">
                {job.experience_years} yrs
              </span>
            )} */}
            {job.hit_count > 1 && (
              <span
                title={`Matched by: ${(job.matched_queries || []).join(", ")}`}
                className="rounded-md border border-amber-400/20 bg-amber-500/10 px-2 py-1 text-[10px] text-amber-300"
              >
                {job.hit_count}x query hits
              </span>
            )}
            <a
              href={job.url}
              target="_blank"
              rel="noopener noreferrer"
              className="ml-auto inline-flex items-center gap-1.5 rounded-lg border border-white/10 px-3 py-2 text-xs font-medium text-slate-300 transition hover:bg-white/5"
            >
              View
              <ExternalLink className="h-3 w-3" />
            </a>
            {alreadyApplied ? (
              <span className="inline-flex items-center gap-1.5 rounded-lg border border-emerald-400/20 bg-emerald-500/10 px-3 py-2 text-xs font-semibold text-emerald-300">
                <CheckCircle2 className="h-3.5 w-3.5" />
                Applied
              </span>
            ) : (
              <button
                type="button"
                onClick={onApply}
                disabled={applying}
                className="inline-flex items-center gap-1.5 rounded-lg bg-emerald-400 px-3 py-2 text-xs font-semibold text-[#07100c] transition hover:bg-emerald-300 disabled:opacity-60"
              >
                {applying ? (
                  <LoaderCircle className="h-3.5 w-3.5 animate-spin" />
                ) : null}
                Apply
              </button>
            )}
          </div>
          {applyError && (
            <p className="mt-2 text-[11px] text-rose-300">{applyError}</p>
          )}
        </div>
      </div>
    </article>
  );
}

function SearchingState({ googleEnabled }: { googleEnabled?: boolean }) {
  return (
    <div className="rounded-2xl border border-white/8 bg-white/[0.03] px-6 py-16 text-center">
      <div className="mx-auto mb-5 flex h-14 w-14 items-center justify-center rounded-2xl bg-emerald-400/8">
        <LoaderCircle className="h-7 w-7 animate-spin text-emerald-400" />
      </div>
      <p className="font-medium text-white">
        {googleEnabled
          ? "Searching Google + company job boards"
          : "Searching company job boards"}
      </p>
      <p className="mt-2 text-xs text-slate-500">
        {googleEnabled
          ? "Pulling Google organic results for each ATS dork, then checking each posting is still open..."
          : "Running query permutations in parallel, then checking each posting is still open..."}
      </p>
    </div>
  );
}

function EmptyState() {
  return (
    <div className="grid gap-3 sm:grid-cols-3">
      {[
        [Target, "Relevance ranked", "Role and skill matching, not just keywords"],
        [Building2, "Direct sources", "Only known ATS and company career URLs"],
        [Filter, "Powerful filters", "Date, work type, source, remote and match score"],
      ].map(([Icon, title, copy]) => {
        const FeatureIcon = Icon as typeof Target;
        return (
          <div
            key={title as string}
            className="rounded-xl border border-white/8 bg-white/[0.025] p-5"
          >
            <FeatureIcon className="mb-3 h-5 w-5 text-emerald-400" />
            <p className="text-sm font-medium text-slate-200">{title as string}</p>
            <p className="mt-1 text-xs leading-5 text-slate-500">{copy as string}</p>
          </div>
        );
      })}
    </div>
  );
}
