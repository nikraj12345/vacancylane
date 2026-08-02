export interface AtsSource {
  slug: string;
  name: string;
}

export interface JobListing {
  title: string;
  url: string;
  snippet: string;
  source: string;
  source_name: string;
  company: string | null;
  location: string | null;
  location_match: "match" | "remote" | "country" | "unknown" | "mismatch";
  location_hint: string | null;
  is_remote: boolean;
  employment_type: string | null;
  experience_match: "match" | "unknown" | "mismatch";
  experience_years: string | null;
  posted_text: string | null;
  posted_at: string | null;
  relevance_score: number;
  hit_count: number;
  matched_queries: string[];
  status: "open" | "unknown";
  verified: boolean;
}

export interface QueryUsed {
  source: string;
  source_name: string;
  label: string;
  query: string;
}

export interface JobSearchLocation {
  label: string;
  city: string;
  state: string;
  country: string;
  remote: boolean;
}

export interface JobSearchRequest {
  role: string;
  location?: string;
  locations?: JobSearchLocation[];
  skills?: string;
  experience?: string;
  experience_bands?: string[];
  alternate_role?: string;
  company?: string;
  sources?: string[];
  max_per_source?: number;
  date_posted?: "any" | "day" | "week" | "month" | "year";
  remote_only?: boolean;
  employment_type?: "" | "Full-time" | "Part-time" | "Contract";
  verify_live?: boolean;
  raw_results?: boolean;
}

export interface GoogleSearchLink {
  source: string;
  source_name: string;
  label: string;
  query: string;
  google_url: string;
}

export interface GoogleLinksResponse {
  combined_query: string;
  combined_google_url: string;
  links: GoogleSearchLink[];
  count: number;
}

export interface JobSearchResponse {
  total: number;
  jobs: JobListing[];
  queries_used: QueryUsed[];
  query_count: number;
  removed_closed: number;
  search_providers: string[];
  google_enabled: boolean;
  raw_results: boolean;
  variables: Record<string, string>;
}

export interface SearchStatus {
  google_enabled: boolean;
  providers: string[];
  setup_hint: string;
}

export interface ResumeLocation {
  label: string;
  city: string;
  state: string;
  country: string;
  remote: boolean;
}

export interface ResumeProfile {
  role: string;
  alternate_role: string;
  skills: string[];
  skills_text: string;
  experience_years: number | null;
  experience_bands: string[];
  locations: ResumeLocation[];
  summary: string;
  warnings: string[];
}

export interface User {
  id: number;
  email: string;
  name: string | null;
  picture_url: string | null;
}

export interface AuthStatus {
  google_login_enabled: boolean;
  google_client_id: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface Application {
  id: number;
  job_url: string;
  job_title: string;
  company: string | null;
  location: string | null;
  source: string | null;
  source_name: string | null;
  status: string;
  applied_at: string;
  notes: string | null;
}

export interface ApplicationListResponse {
  total: number;
  applications: Application[];
}

export interface SavedSearch {
  id: string;
  role: string;
  alternate_role: string | null;
  location_label: string | null;
  skills: string | null;
  company: string | null;
  experience_bands: string[];
  sources: string[];
  payload: Record<string, unknown>;
  result_count: number;
  results_json?: JobListing[];
  created_at: string;
}

export interface SavedSearchListResponse {
  total: number;
  searches: SavedSearch[];
}
