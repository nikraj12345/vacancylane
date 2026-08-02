"""Run multiple ATS query permutations and return ranked job listings."""

from __future__ import annotations

import re
import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta, timezone
from threading import Lock
from urllib.parse import urlparse

from ddgs import DDGS

from app.services.experience_match import (
    MATCH_MISMATCH as EXP_MISMATCH,
    MATCH_UNKNOWN as EXP_UNKNOWN,
    experience_query_clause,
    match_experience,
)
from app.services.google_search import google_search_available, search_google
from app.services.job_liveness import verify_jobs
from app.services.location_match import (
    MATCH_MISMATCH,
    MATCH_UNKNOWN,
    is_remote_text,
    match_location,
    match_rank,
)

logger = logging.getLogger("uvicorn.error")

ATS_SITES: dict[str, dict] = {
    "greenhouse": {
        "name": "Greenhouse",
        "host_hint": "greenhouse",
        "sites": [
            "job-boards.greenhouse.io",
            "boards.greenhouse.io",
        ],
    },
    "lever": {
        "name": "Lever",
        "host_hint": "lever.co",
        "sites": ["jobs.lever.co"],
    },
    "ashby": {
        "name": "Ashby",
        "host_hint": "ashbyhq.com",
        "sites": ["jobs.ashbyhq.com"],
    },
    "workday": {
        "name": "Workday",
        "host_hint": "myworkdayjobs.com",
        "sites": ["myworkdayjobs.com"],
    },
    "smartrecruiters": {
        "name": "SmartRecruiters",
        "host_hint": "smartrecruiters.com",
        "sites": ["jobs.smartrecruiters.com"],
    },
    "workable": {
        "name": "Workable",
        "host_hint": "workable.com",
        "sites": ["apply.workable.com"],
    },
    "linkedin": {
        "name": "LinkedIn",
        "host_hint": "linkedin.com",
        "sites": ["linkedin.com/jobs"],
    },
    "wellfound": {
        "name": "Wellfound",
        "host_hint": "wellfound.com",
        "sites": ["wellfound.com/jobs", "wellfound.com"],
    },
    "instahyre": {
        "name": "Instahyre",
        "host_hint": "instahyre.com",
        "sites": ["instahyre.com"],
    },
    "teamtailor": {
        "name": "Teamtailor",
        "host_hint": "teamtailor.com",
        "sites": ["teamtailor.com"],
    },
    "bamboohr": {
        "name": "BambooHR",
        "host_hint": "bamboohr.com",
        "sites": ["bamboohr.com"],
    },
}

HOST_TO_SOURCE = {
    "greenhouse.io": "greenhouse",
    "job-boards.greenhouse.io": "greenhouse",
    "boards.greenhouse.io": "greenhouse",
    "lever.co": "lever",
    "jobs.lever.co": "lever",
    "ashbyhq.com": "ashby",
    "jobs.ashbyhq.com": "ashby",
    "myworkdayjobs.com": "workday",
    "wd1.myworkdayjobs.com": "workday",
    "wd5.myworkdayjobs.com": "workday",
    "smartrecruiters.com": "smartrecruiters",
    "jobs.smartrecruiters.com": "smartrecruiters",
    "workable.com": "workable",
    "apply.workable.com": "workable",
    "linkedin.com": "linkedin",
    "wellfound.com": "wellfound",
    "angel.co": "wellfound",
    "angel.com": "wellfound",
    "instahyre.com": "instahyre",
    "teamtailor.com": "teamtailor",
    "bamboohr.com": "bamboohr",
}

ROLE_STOP_WORDS = {
    "engineer",
    "engineering",
    "developer",
    "software",
    "senior",
    "junior",
    "staff",
    "lead",
    "principal",
    "associate",
    "the",
    "and",
    "or",
    "with",
}

ROLE_EXPANSIONS: dict[str, list[str]] = {
    "ai engineer": [
        "AI Engineer",
        "Machine Learning Engineer",
        "ML Engineer",
        "LLM Engineer",
        "Applied AI Engineer",
        "Generative AI Engineer",
    ],
    "ml engineer": [
        "ML Engineer",
        "Machine Learning Engineer",
        "AI Engineer",
        "Applied Scientist",
    ],
    "backend engineer": [
        "Backend Engineer",
        "Backend Developer",
        "Software Engineer Backend",
        "Server Engineer",
        "API Engineer",
    ],
    "full stack": [
        "Full Stack Engineer",
        "Fullstack Engineer",
        "Full Stack Developer",
        "Software Engineer",
    ],
    "frontend engineer": [
        "Frontend Engineer",
        "Front End Engineer",
        "UI Engineer",
        "React Engineer",
    ],
    "devops": [
        "DevOps Engineer",
        "SRE",
        "Platform Engineer",
        "Infrastructure Engineer",
    ],
    "data engineer": [
        "Data Engineer",
        "Analytics Engineer",
        "ETL Engineer",
    ],
}


def detect_source(url: str) -> str | None:
    try:
        host = urlparse(url).netloc.lower().removeprefix("www.")
    except Exception:
        return None
    if host in HOST_TO_SOURCE:
        return HOST_TO_SOURCE[host]
    for suffix, slug in HOST_TO_SOURCE.items():
        if host.endswith(suffix):
            return slug
    return None


def _words(value: str) -> set[str]:
    return set(re.findall(r"[a-z0-9+#.]+", value.lower()))


def _split_skills(skills: str) -> list[str]:
    if not skills.strip():
        return []
    parts = re.split(r"\s+OR\s+|,|/|\|", skills, flags=re.I)
    cleaned = [part.strip(" ()\"'") for part in parts if part.strip(" ()\"'")]
    # Preserve unique order
    seen: set[str] = set()
    out: list[str] = []
    for part in cleaned:
        key = part.lower()
        if key not in seen:
            seen.add(key)
            out.append(part)
    return out


def _role_variants(role: str, alternate_role: str) -> list[str]:
    variants: list[str] = []
    for value in (role, alternate_role):
        value = (value or "").strip()
        if value and value.lower() not in {v.lower() for v in variants}:
            variants.append(value)

    key = role.strip().lower()
    for pattern, expansions in ROLE_EXPANSIONS.items():
        if pattern in key or key in pattern:
            for expansion in expansions:
                if expansion.lower() not in {v.lower() for v in variants}:
                    variants.append(expansion)

    # Soften seniority for broader coverage
    softened = re.sub(
        r"\b(senior|junior|staff|principal|lead)\b\s*",
        "",
        role,
        flags=re.I,
    ).strip()
    if softened and softened.lower() not in {v.lower() for v in variants}:
        variants.append(softened)

    return variants[:6]


def _clean_query(query: str) -> str:
    query = re.sub(r"\(\s*\)", "", query)
    query = re.sub(r'""', "", query)
    query = re.sub(r"\s{2,}", " ", query)
    return query.strip()


def _location_terms(location: str) -> list[str]:
    """Split a location clause like '("Bengaluru" OR "Remote")' into terms."""
    raw = (location or "").strip()
    if not raw:
        return []
    # Pull quoted terms first
    quoted = re.findall(r'"([^"]+)"', raw)
    if quoted:
        return quoted
    # Fallback: split on OR / commas
    parts = re.split(r"\s+OR\s+|,", raw, flags=re.I)
    return [part.strip(" ()") for part in parts if part.strip(" ()")]


def build_query_permutations(
    *,
    site: str,
    role: str,
    alternate_role: str,
    location: str,
    skills: str,
    experience: str,
    company: str,
    remote_only: bool,
    employment_type: str,
) -> list[dict[str, str]]:
    """Build multiple complementary query shapes for broader recall."""
    roles = _role_variants(role, alternate_role)
    skill_list = _split_skills(skills)
    location_terms = _location_terms(location)
    location_clause = location.strip()
    company = company.strip()

    primary = roles[0] if roles else role
    secondary = roles[1] if len(roles) > 1 else ""
    skill_or = " OR ".join(skill_list[:4])
    top_skills = skill_list[:2]
    site_clause = f"site:{site}"

    candidates: list[tuple[str, str]] = []

    # 1) Exact role on site
    candidates.append(("exact_role", f'{site_clause} "{primary}"'))

    # 2) Role OR alternate
    if secondary:
        candidates.append(
            (
                "role_or_alt",
                f'{site_clause} ("{primary}" OR "{secondary}")',
            )
        )

    # 3) Role + combined locations
    if location_clause:
        candidates.append(
            ("role_location", f'{site_clause} "{primary}" {location_clause}')
        )

    # 3b) Role + each location individually (multi-select expansion)
    for term in location_terms[:5]:
        candidates.append(
            (
                "role_one_location",
                f'{site_clause} "{primary}" "{term}"',
            )
        )
        if secondary:
            candidates.append(
                (
                    "alt_one_location",
                    f'{site_clause} "{secondary}" "{term}"',
                )
            )

    # 4) Role + skills block
    if skill_or:
        candidates.append(
            ("role_skills", f'{site_clause} "{primary}" ({skill_or})')
        )

    # 5) Role + location + skills
    if location_clause and skill_or:
        candidates.append(
            (
                "full",
                f'{site_clause} {location_clause} ("{primary}"'
                + (f' OR "{secondary}"' if secondary else "")
                + f") ({skill_or})",
            )
        )

    # 6) Title-focused search (often more precise)
    candidates.append(
        ("intitle", f'{site_clause} intitle:"{primary}"')
    )
    if secondary:
        candidates.append(
            ("intitle_alt", f'{site_clause} intitle:"{secondary}"')
        )

    # 7) Each top skill with role
    for skill in top_skills:
        candidates.append(
            ("role_skill", f'{site_clause} "{primary}" "{skill}"')
        )

    # 8) Alternate role alone
    if secondary:
        candidates.append(("alt_only", f'{site_clause} "{secondary}"'))
        if location_clause:
            candidates.append(
                (
                    "alt_location",
                    f'{site_clause} "{secondary}" {location_clause}',
                )
            )

    # 9) Company-targeted
    if company:
        candidates.append(
            ("company", f'{site_clause} "{company}" "{primary}"')
        )

    # Experience is deliberately NOT put in the query. Requiring a literal
    # "0-2 years" to appear in Google's index takes a query from ~10 hits to 0,
    # because postings phrase experience in dozens of ways. The selected bands
    # are enforced afterwards by _apply_experience_filter, which reads the
    # years out of the posting text instead.

    # 10) Broader role family without quotes on long titles
    short_role = " ".join(primary.split()[:2])
    if short_role.lower() != primary.lower():
        candidates.append(("short_role", f"{site_clause} {short_role}"))

    # Apply shared modifiers once, then dedupe
    queries: list[dict[str, str]] = []
    seen: set[str] = set()
    for label, base in candidates:
        query = base
        if remote_only and "remote" not in query.lower():
            query += " remote"
        # Always exclude internships — they aren't a selectable employment type.
        query += " -internship -intern"
        if employment_type:
            query += f' "{employment_type}"'
        query = _clean_query(query)
        key = query.lower()
        if key in seen or len(query) < 12:
            continue
        seen.add(key)
        queries.append({"label": label, "query": query})

    # Cap permutations so each wave stays manageable under parallel load
    return queries[:10]


PREFERRED_GOOGLE_LABELS = (
    "role_location",
    "exact_role",
    "role_or_alt",
    "intitle",
    "full",
)


def google_search_url(query: str, date_posted: str = "any") -> str:
    """Build a google.com search URL for a dork query."""
    from urllib.parse import urlencode

    params: dict[str, str] = {"q": query}
    tbs = {
        "day": "qdr:d",
        "week": "qdr:w",
        "month": "qdr:m",
        "year": "qdr:y",
    }.get(date_posted)
    if tbs:
        params["tbs"] = tbs
    return f"https://www.google.com/search?{urlencode(params)}"


def build_google_search_links(
    *,
    role: str,
    location: str = "",
    skills: str = "",
    experience: str = "",
    experience_bands: list[str] | None = None,
    alternate_role: str = "",
    company: str = "",
    sources: list[str] | None = None,
    date_posted: str = "month",
    remote_only: bool = False,
    employment_type: str = "",
) -> dict:
    """Return Google search URLs for the same ATS dorks the app would run."""
    selected = sources or list(ATS_SITES.keys())
    selected = [s for s in selected if s in ATS_SITES]
    if not selected:
        selected = list(ATS_SITES.keys())

    bands = [band for band in (experience_bands or []) if band]
    experience_clause = experience_query_clause(bands) or experience.strip()

    links: list[dict] = []
    for slug in selected:
        meta = ATS_SITES[slug]
        best: dict[str, str] | None = None
        best_rank = len(PREFERRED_GOOGLE_LABELS) + 1
        for site in meta["sites"]:
            perms = build_query_permutations(
                site=site,
                role=role,
                alternate_role=alternate_role or role,
                location=location,
                skills=skills,
                experience=experience_clause,
                company=company,
                remote_only=remote_only,
                employment_type=employment_type,
            )
            for perm in perms:
                try:
                    rank = PREFERRED_GOOGLE_LABELS.index(perm["label"])
                except ValueError:
                    rank = len(PREFERRED_GOOGLE_LABELS)
                if rank < best_rank:
                    best_rank = rank
                    best = {
                        "source": slug,
                        "source_name": meta["name"],
                        "label": perm["label"],
                        "query": perm["query"],
                        "google_url": google_search_url(
                            perm["query"], date_posted
                        ),
                    }
        if best:
            links.append(best)

    # One combined Google search covering every selected ATS board.
    site_clause = " OR ".join(
        f"site:{site}"
        for slug in selected
        for site in ATS_SITES[slug]["sites"][:1]
    )
    combined_parts = [f"({site_clause})", f'"{role.strip()}"']
    if location.strip():
        combined_parts.append(location.strip())
    # Experience is left out on purpose — see build_query_permutations.
    if remote_only:
        combined_parts.append("remote")
    if employment_type:
        combined_parts.append(f'"{employment_type}"')
    combined_parts.append("-internship -intern")
    combined_query = _clean_query(" ".join(combined_parts))

    return {
        "combined_query": combined_query,
        "combined_google_url": google_search_url(combined_query, date_posted),
        "links": links,
        "count": len(links),
    }


# High-signal shapes — executed first in parallel across all ATS sources.
PRIORITY_LABELS = {
    "exact_role",
    "role_or_alt",
    "role_location",
    "intitle",
    "role_skills",
    "full",
}


# Engine names must exist in DDGS's registry: an unknown name (the old "bing")
# makes DDGS fall back to "auto" and call random engines. Ordered by measured
# yield on ATS dork queries. Startpage and DuckDuckGo are excluded: the former
# refuses connections here, the latter is slow and returns nothing for site:.
SEARCH_BACKENDS = ("yandex", "yahoo", "brave", "mojeek")

# Engines are merged rather than raced: each one indexes a different slice of
# the ATS sites, so the union is roughly twice what the first responder alone
# returns. A narrow dork can legitimately return nothing everywhere, so cap the
# attempts to keep a dead query from walking the whole list.
MAX_ENGINE_ATTEMPTS = 4

# Engines cap a single response at roughly one page, so extra results only come
# from paging. Yahoo pages reliably; the others usually stop after page 1, which
# the loop detects and moves on from.
MAX_SEARCH_PAGES = 3

# Liveness, location and experience filtering routinely discard half the
# candidates, so wave 1 has to clear a high bar before wave 2 is skipped.
SECONDARY_WAVE_THRESHOLD = 120

# An engine that cannot be reached is skipped for a while rather than retried
# by all ~30 queries in a wave.
ENGINE_FAILURE_LIMIT = 2
ENGINE_COOLDOWN_SECONDS = 300.0

_engine_lock = Lock()
_engine_failures: dict[str, int] = {}
_engine_blocked_until: dict[str, float] = {}

_TRANSPORT_ERROR_MARKERS = (
    "connecterror",
    "connection refused",
    "timed out",
    "timeout",
    "temporary failure",
    "name resolution",
    "ssl",
)


def _is_transport_error(exc: Exception) -> bool:
    """Distinguish an unreachable engine from one that simply found nothing."""
    text = f"{type(exc).__name__}: {exc}".lower()
    if "no results found" in text:
        return False
    return any(marker in text for marker in _TRANSPORT_ERROR_MARKERS)


def _engine_available(backend: str) -> bool:
    with _engine_lock:
        blocked_until = _engine_blocked_until.get(backend, 0.0)
        if blocked_until and time.monotonic() < blocked_until:
            return False
        if blocked_until:
            # Cooldown elapsed — give the engine another chance.
            _engine_blocked_until.pop(backend, None)
            _engine_failures.pop(backend, None)
        return True


def _record_engine_failure(backend: str, exc: Exception) -> None:
    with _engine_lock:
        failures = _engine_failures.get(backend, 0) + 1
        _engine_failures[backend] = failures
        newly_blocked = (
            failures >= ENGINE_FAILURE_LIMIT and backend not in _engine_blocked_until
        )
        if newly_blocked:
            _engine_blocked_until[backend] = (
                time.monotonic() + ENGINE_COOLDOWN_SECONDS
            )
    # Log once per trip instead of once per query, which is what flooded the logs.
    if newly_blocked:
        logger.warning(
            "SEARCH ENGINE disabled for %.0fs | provider=%s | error=%s",
            ENGINE_COOLDOWN_SECONDS,
            backend,
            exc,
        )


def _record_engine_success(backend: str) -> None:
    with _engine_lock:
        _engine_failures.pop(backend, None)
        _engine_blocked_until.pop(backend, None)


def relax_query(query: str) -> str:
    """Loosen an over-constrained dork so it stops returning zero documents.

    Stacked exact phrases are what make Google answer "did not match any
    documents". The site: filter and the role phrase carry the intent, so the
    rest is dropped: OR groups first, then quotes around every later phrase.
    """
    relaxed = re.sub(r"\([^)]*\)", " ", query)

    def unquote_after_first(text: str) -> str:
        seen_first = False
        parts: list[str] = []
        for chunk in re.split(r'("[^"]*")', text):
            if chunk.startswith('"') and chunk.endswith('"') and len(chunk) > 1:
                if seen_first:
                    parts.append(chunk.strip('"'))
                    continue
                seen_first = True
            parts.append(chunk)
        return "".join(parts)

    relaxed = unquote_after_first(relaxed)
    return _clean_query(relaxed)


def _run_query(
    query: str, max_results: int, date_posted: str
) -> tuple[dict[str, dict], list[str]]:
    """Run one exact query across Google and the DDGS engines."""
    collected: dict[str, dict] = {}
    providers: list[str] = []

    if google_search_available():
        google_hits, google_provider = search_google(
            query, max_results=max_results, date_posted=date_posted
        )
        for item in google_hits:
            href = item.get("href")
            if href and href not in collected:
                collected[href] = item
        if google_hits:
            providers.append(google_provider)

        # Google already returned a full page — skip the slower DDGS merge so
        # Serper credits and wall-clock aren't spent twice for the same slice.
        if len(collected) >= max(10, max_results // 2):
            return collected, providers

    time_limits = {"day": "d", "week": "w", "month": "m", "year": "y"}
    # Only apply date filter for short windows; month/year often returns empty for ATS pages
    # and just wastes a round-trip before the fallback.
    timelimit = time_limits.get(date_posted) if date_posted in {"day", "week"} else None

    attempts = 0

    for backend in SEARCH_BACKENDS:
        if attempts >= MAX_ENGINE_ATTEMPTS or len(collected) >= max_results:
            break
        if not _engine_available(backend):
            continue
        attempts += 1
        engine_hits = 0

        for page in range(1, MAX_SEARCH_PAGES + 1):
            try:
                with DDGS(timeout=5) as ddgs:
                    kwargs: dict = {
                        "max_results": max_results,
                        "backend": backend,
                        "page": page,
                    }
                    if timelimit:
                        kwargs["timelimit"] = timelimit
                    results = list(ddgs.text(query, **kwargs) or [])
            except Exception as exc:
                if _is_transport_error(exc):
                    _record_engine_failure(backend, exc)
                elif page == 1:
                    logger.debug(
                        "No results | provider=%s | query=%r", backend, query
                    )
                break

            fresh = 0
            for item in results:
                href = item.get("href")
                if href and href not in collected:
                    collected[href] = item
                    fresh += 1
            engine_hits += len(results)

            # An engine that repeats a page or runs dry has nothing left to give.
            if not results or fresh == 0:
                break
            if len(collected) >= max_results:
                break

        if engine_hits:
            _record_engine_success(backend)
            providers.append(f"ddgs:{backend}")

    return collected, providers


def _search_one(
    query: str, max_results: int, date_posted: str = "month"
) -> tuple[list[dict], str]:
    """Collect results for one query, preferring Google when configured.

    Google cannot be scraped directly — when a Serper or CSE key is present we
    pull real Google organic hits first, then merge DDGS engines for extra
    coverage. Without a key, behaviour is DDGS-only.

    A query that matches nothing anywhere is retried once in relaxed form, so a
    single over-specific phrase cannot silently contribute zero jobs.
    """
    collected, providers = _run_query(query, max_results, date_posted)

    if not collected:
        relaxed = relax_query(query)
        if relaxed and relaxed.lower() != query.lower():
            logger.info(
                "QUERY relaxed | original=%r | retry=%r", query, relaxed
            )
            collected, providers = _run_query(relaxed, max_results, date_posted)
            if collected:
                providers = [f"{p}(relaxed)" for p in providers]

    if not collected:
        return [], "none"
    return list(collected.values()), "+".join(providers)


# Workday, Teamtailor and BambooHR put the employer in the subdomain and start
# the path with a locale or a literal "jobs", so the first path segment is never
# the company name for them.
_SUBDOMAIN_SOURCES = {"workday", "teamtailor", "bamboohr"}
_LOCALE_SEGMENT = re.compile(r"^[a-z]{2}([-_][a-z0-9]{2,4})?$", re.I)
_PATH_NOISE = {
    "jobs",
    "careers",
    "job",
    "embed",
    "en",
    "career",
    "openings",
    "view",
    "role",
    "l",
    "company",
}


def _company_from_url(url: str, source: str) -> str | None:
    parsed = urlparse(url)

    if source in _SUBDOMAIN_SOURCES:
        label = parsed.hostname.split(".")[0] if parsed.hostname else ""
        if label and label != "www":
            return label.replace("-", " ").title()

    path = [part for part in parsed.path.strip("/").split("/") if part]

    if source == "instahyre":
        for segment in path:
            lowered = segment.lower()
            if lowered.startswith("job-") and "-at-" in lowered:
                company = segment.split("-at-", 1)[-1].replace("-", " ").strip()
                return company.title() if company else None

    if source == "linkedin":
        # LinkedIn job URLs rarely encode the employer; title/snippet do.
        return None

    for segment in path:
        if segment.lower() in _PATH_NOISE or _LOCALE_SEGMENT.match(segment):
            continue
        # A bare id is a posting reference, not an employer.
        if segment.isdigit():
            continue
        if segment.lower().startswith("job-"):
            continue
        return segment.replace("-", " ").title()
    return None


def _clean_listing(title: str, company: str | None) -> tuple[str, str | None]:
    cleaned = re.sub(r"^Job Application for\s+", "", title, flags=re.I)
    cleaned = re.sub(r"\s*-\s*jobs\.[^\s]+$", "", cleaned, flags=re.I)
    title_company = re.search(r"\s+at\s+(.+)$", cleaned, flags=re.I)
    if title_company:
        inferred = title_company.group(1).strip(" .-|")
        cleaned = cleaned[: title_company.start()].strip()
        if inferred and len(inferred) < 100:
            company = inferred
    if company:
        prefix = re.compile(rf"^{re.escape(company)}\s*[-–—|]\s*", re.I)
        cleaned = prefix.sub("", cleaned)
    return cleaned.strip(), company


def _is_job_url(url: str, source: str) -> bool:
    path = urlparse(url).path.lower().strip("/")
    parts = [part for part in path.split("/") if part]
    if not parts:
        return False
    if source in {"lever", "ashby", "smartrecruiters"}:
        return len(parts) >= 2
    if source == "greenhouse":
        return "jobs" in parts or any(part.isdigit() for part in parts)
    if source == "workday":
        return "/job/" in f"/{path}/" or "/jobs/" in f"/{path}/"
    if source == "workable":
        return "/j/" in f"/{path}/" or len(parts) >= 2
    if source == "linkedin":
        # /jobs/view/<id> or /jobs/view/<slug>-<id>
        return "jobs" in parts and "view" in parts and len(parts) >= 3
    if source == "wellfound":
        # /jobs/<slug>, /role/<slug>, or company job paths
        return (
            ("jobs" in parts and len(parts) >= 2)
            or ("role" in parts and len(parts) >= 2)
            or ("l" in parts and len(parts) >= 2)
        )
    if source == "instahyre":
        # /job-<id>-title-at-company/ or /jobs/...
        return any(part.startswith("job-") for part in parts) or (
            "jobs" in parts and len(parts) >= 2
        )
    if source == "teamtailor":
        return "jobs" in parts or len(parts) >= 2
    if source == "bamboohr":
        return "careers" in parts and len(parts) >= 2
    return False


def _score_job(
    title: str,
    snippet: str,
    *,
    role: str,
    alternate_role: str,
    location: str,
    skills: str,
    company: str,
    experience: str = "",
    experience_bands: list[str] | None = None,
    hit_count: int = 1,
) -> int:
    title_l = title.lower()
    text_l = f"{title} {snippet}".lower()
    role_l = role.lower().strip()
    alternate_l = alternate_role.lower().strip()
    score = 15

    if role_l and role_l in title_l:
        score += 45
    elif alternate_l and alternate_l in title_l:
        score += 40
    else:
        role_words = _words(role) - ROLE_STOP_WORDS
        alternate_words = _words(alternate_role) - ROLE_STOP_WORDS
        discriminators = role_words | alternate_words
        title_hits = len(discriminators & _words(title))
        body_hits = len(discriminators & _words(snippet))
        score += min(30, title_hits * 15 + body_hits * 5)

    skill_terms = {
        word for word in _words(skills) if word not in {"or", "and", "with"}
    }
    score += min(15, len(skill_terms & _words(text_l)) * 5)

    if location and location.lower() in text_l:
        score += 10
    else:
        # Multi-location: score if any quoted location term appears
        for term in re.findall(r'"([^"]+)"', location):
            if term.lower() in text_l:
                score += 8
                break
    if experience_bands:
        verdict, _ = match_experience(text_l, experience_bands)
        if verdict == "match":
            score += 12
        elif verdict == "mismatch":
            score -= 25
    elif experience:
        years = re.findall(r"\d+", experience)
        if years and any(year in text_l for year in years):
            score += 6
    if company and company.lower() in text_l:
        score += 15
    if any(word in text_l for word in ("apply", "job", "position", "role")):
        score += 5

    # Boost jobs discovered by multiple query variants
    score += min(20, max(0, hit_count - 1) * 8)
    return min(score, 100)


def _is_relevant(title: str, snippet: str, role: str, alternate_role: str) -> bool:
    text_words = _words(f"{title} {snippet}")
    specific = (
        (_words(role) | _words(alternate_role))
        - ROLE_STOP_WORDS
    )
    if specific:
        return bool(specific & text_words)
    return bool((_words(role) | _words(alternate_role)) & _words(title))


def _extract_posted_text(text: str) -> tuple[str | None, str | None]:
    patterns = [
        (r"\b(today|just posted)\b", 0),
        (r"\b(\d+)\s+hours?\s+ago\b", 0),
        (r"\b(\d+)\s+days?\s+ago\b", None),
        (r"\b(\d+)\s+weeks?\s+ago\b", None),
    ]
    lower = text.lower()
    now = datetime.now(timezone.utc)
    for pattern, fixed_days in patterns:
        match = re.search(pattern, lower)
        if not match:
            continue
        label = match.group(0).title()
        if fixed_days is not None:
            date = now - timedelta(days=fixed_days)
        elif "day" in label.lower():
            date = now - timedelta(days=int(match.group(1)))
        else:
            date = now - timedelta(weeks=int(match.group(1)))
        return label, date.isoformat()
    return None, None


def _employment_type(text: str) -> str | None:
    lower = text.lower()
    for needle, label in (
        ("full-time", "Full-time"),
        ("full time", "Full-time"),
        ("part-time", "Part-time"),
        ("part time", "Part-time"),
        ("contract", "Contract"),
        ("internship", "Internship"),
        ("intern", "Internship"),
    ):
        if needle in lower:
            return label
    return None


JUNK_TITLES = {
    "careers",
    "career",
    "jobs",
    "job",
    "job board",
    "open positions",
    "current openings",
    "home",
    "apply",
}


def _is_junk_title(title: str) -> bool:
    """Search snippets sometimes yield a bare host or a board landing page."""
    cleaned = title.strip().lower()
    if not cleaned or len(cleaned) < 3:
        return True
    if cleaned in JUNK_TITLES:
        return True
    if re.match(r"^(https?://|www\.)", cleaned):
        return True
    # A title that is really just the posting's host, e.g.
    # "nvidia.wd5.myworkdayjobs.com/en-US/NVIDIAExternalCareerSite/job/...".
    first_token = cleaned.split()[0]
    if "." in first_token and "/" in first_token:
        return True
    return bool(
        re.fullmatch(r"[a-z0-9.-]+\.(com|io|co|net|org|ai|jobs)", first_token)
    )


def _snippet_location(job: dict) -> str | None:
    """Best-effort location when the ATS did not give us one."""
    text = f"{job.get('title', '')} {job.get('snippet', '')}"
    match = re.search(
        r"\b(?:location|located in|based in)\s*[:\-]?\s*([A-Za-z .'\-]{3,40})",
        text,
        flags=re.I,
    )
    if match:
        return match.group(1).strip(" .-")
    return None


def annotate_locations(
    jobs: list[dict], location_filters: list[dict] | None, raw: bool = False
) -> list[dict]:
    """Label how each job's location relates to the request, dropping nothing.

    Location is reported, never filtered on: a mismatch is shown as such and
    the UI's "In my locations" toggle can hide it on demand. Junk rows that are
    not job postings at all are still removed.
    """
    for job in jobs:
        if not job.get("location"):
            job["location"] = _snippet_location(job)
        if not job.get("is_remote"):
            job["is_remote"] = is_remote_text(
                f"{job.get('location') or ''} {job.get('title', '')}"
            )

    if raw:
        for job in jobs:
            job["location_match"] = MATCH_UNKNOWN
        return jobs

    kept = [job for job in jobs if not _is_junk_title(job.get("title", ""))]
    for job in kept:
        job["location_match"] = (
            match_location(
                job.get("location"),
                bool(job.get("is_remote")),
                location_filters,
            )
            if location_filters
            else MATCH_UNKNOWN
        )
    return kept


def annotate_experience(
    jobs: list[dict], experience_bands: list[str] | None, raw: bool = False
) -> list[dict]:
    """Label the years each posting asks for, dropping nothing."""
    if raw or not experience_bands:
        for job in jobs:
            job["experience_match"] = EXP_UNKNOWN
            job.setdefault("experience_years", None)
        return jobs

    for job in jobs:
        text = f"{job.get('title', '')} {job.get('snippet', '')}"
        verdict, extracted = match_experience(text, experience_bands)
        job["experience_match"] = verdict
        job["experience_years"] = (
            f"{extracted[0]:g}-{extracted[1]:g}" if extracted else None
        )
    return jobs


def search_jobs(
    *,
    role: str,
    location: str = "",
    skills: str = "",
    experience: str = "",
    experience_bands: list[str] | None = None,
    alternate_role: str = "",
    company: str = "",
    sources: list[str] | None = None,
    max_per_source: int = 8,
    date_posted: str = "month",
    remote_only: bool = False,
    employment_type: str = "",
    verify_live: bool = True,
    location_filters: list[dict] | None = None,
    raw_results: bool = False,
) -> dict:
    search_started = time.perf_counter()

    # Raw mode answers "just show me everything the search returned": no
    # liveness check, no location or experience filter, no relevance gate.
    if raw_results:
        verify_live = False
    selected = sources or list(ATS_SITES.keys())
    selected = [s for s in selected if s in ATS_SITES]
    if not selected:
        selected = list(ATS_SITES.keys())

    bands = [band for band in (experience_bands or []) if band]
    if not bands and experience.strip():
        # Backward compat: a single free-text value like "3-5 years".
        bands = [experience.strip()]
    experience_clause = experience_query_clause(bands) or experience.strip()

    logger.info(
        "JOB SEARCH started | role=%r | location=%r | skills=%r | "
        "experience_bands=%s | sources=%s | date=%s | verify_live=%s | "
        "raw=%s | google=%s",
        role,
        location,
        skills,
        ",".join(bands) or "-",
        ",".join(selected),
        date_posted,
        verify_live,
        raw_results,
        google_search_available(),
    )

    variables = {
        "role": role,
        "alternate_role": alternate_role or role,
        "location": location,
        "skills": skills,
        "experience": experience_clause,
        "company": company,
    }

    # Build every (source, site, permutation) task up front
    tasks: list[dict] = []
    for slug in selected:
        meta = ATS_SITES[slug]
        for site in meta["sites"]:
            perms = build_query_permutations(
                site=site,
                role=role,
                alternate_role=alternate_role or role,
                location=location,
                skills=skills,
                experience=experience_clause,
                company=company,
                remote_only=remote_only,
                employment_type=employment_type,
            )
            for perm in perms:
                tasks.append(
                    {
                        "slug": slug,
                        "source_name": meta["name"],
                        "site": site,
                        "label": perm["label"],
                        "query": perm["query"],
                    }
                )

    queries_used: list[dict] = []
    # url -> aggregated job dict with hit tracking
    by_url: dict[str, dict] = {}
    providers_seen: set[str] = set()

    def ingest(task: dict, results: list[dict]) -> None:
        slug = task["slug"]
        queries_used.append(
            {
                "source": task["slug"],
                "source_name": task["source_name"],
                "label": task["label"],
                "query": task["query"],
            }
        )
        for item in results:
            url = item.get("href") or item.get("url") or ""
            title = item.get("title") or ""
            snippet = item.get("body") or item.get("description") or ""
            if not url or not title:
                continue

            detected = detect_source(url)
            if raw_results:
                # Keep every hit the engine returned, whatever it points at.
                detected = detected or slug
            else:
                if detected is None:
                    hint = ATS_SITES[slug]["host_hint"]
                    if hint not in url.lower():
                        continue
                    detected = slug
                if detected != slug or not _is_job_url(url, detected):
                    continue
                if not _is_relevant(title, snippet, role, alternate_role or role):
                    continue

            combined = f"{title} {snippet}"
            is_remote = (
                "remote" in combined.lower()
                or "wfh" in combined.lower()
                or "work from home" in combined.lower()
            )
            if remote_only and not raw_results:
                if not (is_remote or "remote" in location.lower()):
                    continue
                is_remote = True

            detected_type = _employment_type(combined)
            if employment_type and detected_type and not raw_results:
                if detected_type.lower() != employment_type.lower():
                    continue

            key = url.split("?")[0].rstrip("/").lower()
            posted_text, posted_at = _extract_posted_text(combined)
            parsed_company = _company_from_url(url, detected)
            cleaned_title, parsed_company = _clean_listing(
                title.strip(), parsed_company
            )

            if key in by_url:
                existing = by_url[key]
                existing["hit_count"] += 1
                existing["matched_queries"].append(task["label"])
                if len(snippet) > len(existing["snippet"]):
                    existing["snippet"] = snippet.strip()
                if len(cleaned_title) > len(existing["title"]):
                    existing["title"] = cleaned_title
                if parsed_company and not existing["company"]:
                    existing["company"] = parsed_company
                if posted_text and not existing["posted_text"]:
                    existing["posted_text"] = posted_text
                    existing["posted_at"] = posted_at
                continue

            by_url[key] = {
                "title": cleaned_title,
                "url": url,
                "snippet": snippet.strip(),
                "source": detected,
                "source_name": ATS_SITES.get(detected, {}).get(
                    "name", detected
                ),
                "company": parsed_company,
                # Real location is filled in from the ATS during verification;
                # the snippet is only a fallback guess.
                "location": None,
                "location_hint": location or None,
                "is_remote": is_remote,
                "employment_type": detected_type,
                "posted_text": posted_text,
                "posted_at": posted_at,
                "hit_count": 1,
                "matched_queries": [task["label"]],
            }

    def run_task(task: dict) -> tuple[dict, list[dict], float, str]:
        # Ask for well beyond the per-source cap: the filters downstream
        # (liveness, location, experience) discard a large share, so a thin
        # candidate pool is what makes the final list look empty.
        per_query = max(20, max_per_source * 3)
        started = time.perf_counter()
        logger.info(
            "QUERY started | source=%s | label=%s | query=%r",
            task["source_name"],
            task["label"],
            task["query"],
        )
        results, provider = _search_one(
            task["query"], per_query, date_posted
        )
        elapsed = time.perf_counter() - started
        logger.info(
            "QUERY finished | source=%s | label=%s | provider=%s | "
            "raw_hits=%d | %.2fs | query=%r",
            task["source_name"],
            task["label"],
            provider,
            len(results),
            elapsed,
            task["query"],
        )
        return task, results, elapsed, provider

    def run_wave(wave_name: str, wave_tasks: list[dict]) -> None:
        if not wave_tasks:
            return
        wave_started = time.perf_counter()
        # I/O-bound: high concurrency finishes the wave near the slowest request.
        workers = min(32, max(8, len(wave_tasks)))
        logger.info(
            "WAVE started | name=%s | queries=%d | workers=%d",
            wave_name,
            len(wave_tasks),
            workers,
        )
        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures = [pool.submit(run_task, task) for task in wave_tasks]
            for fut in as_completed(futures):
                try:
                    task, results, _elapsed, provider = fut.result()
                except Exception:
                    logger.exception("Query worker failed unexpectedly")
                    continue
                for part in provider.split("+"):
                    if part and part != "none":
                        providers_seen.add(part)
                jobs_before = len(by_url)
                ingest(task, results)
                logger.info(
                    "QUERY accepted | source=%s | label=%s | new_jobs=%d | "
                    "unique_jobs_total=%d",
                    task["source_name"],
                    task["label"],
                    len(by_url) - jobs_before,
                    len(by_url),
                )
        logger.info(
            "WAVE finished | name=%s | unique_jobs=%d | %.2fs",
            wave_name,
            len(by_url),
            time.perf_counter() - wave_started,
        )

    # Wave 1: high-signal queries in full parallel across all sources
    priority_tasks = [t for t in tasks if t["label"] in PRIORITY_LABELS][:36]
    secondary_tasks = [t for t in tasks if t["label"] not in PRIORITY_LABELS][:24]

    run_wave("priority", priority_tasks)

    # Wave 2: the filters below cut deeply, so keep widening unless wave 1
    # already produced far more candidates than a page of results needs.
    if len(by_url) < SECONDARY_WAVE_THRESHOLD and secondary_tasks:
        run_wave("secondary", secondary_tasks)
    elif secondary_tasks:
        logger.info(
            "WAVE skipped | name=secondary | unique_jobs=%d meets threshold=%d",
            len(by_url),
            SECONDARY_WAVE_THRESHOLD,
        )
    jobs: list[dict] = []
    for job in by_url.values():
        job["relevance_score"] = _score_job(
            job["title"],
            job["snippet"],
            role=role,
            alternate_role=alternate_role or role,
            location=location,
            skills=skills,
            company=company,
            experience=experience_clause,
            experience_bands=bands,
            hit_count=job["hit_count"],
        )
        jobs.append(job)

    # Soft-dedupe near-identical listings (same title + company, different URL).
    # Raw mode keeps them: it is meant to show everything search returned.
    soft_seen: dict[str, dict] = {}
    for job in [] if raw_results else jobs:
        soft_key = (
            f"{job['title'].lower().strip()}|"
            f"{(job.get('company') or '').lower().strip()}"
        )
        existing = soft_seen.get(soft_key)
        if not existing:
            soft_seen[soft_key] = job
            continue
        # Keep the stronger match; merge hit counts
        existing["hit_count"] += job["hit_count"]
        existing["matched_queries"] = list(
            dict.fromkeys(existing["matched_queries"] + job["matched_queries"])
        )
        if job["relevance_score"] > existing["relevance_score"]:
            job["hit_count"] = existing["hit_count"]
            job["matched_queries"] = existing["matched_queries"]
            soft_seen[soft_key] = job
        else:
            existing["relevance_score"] = _score_job(
                existing["title"],
                existing["snippet"],
                role=role,
                alternate_role=alternate_role or role,
                location=location,
                skills=skills,
                company=company,
                experience=experience_clause,
                experience_bands=bands,
                hit_count=existing["hit_count"],
            )

    if not raw_results:
        jobs = list(soft_seen.values())
    jobs.sort(
        key=lambda j: (
            -j["relevance_score"],
            -j["hit_count"],
            j["title"].lower(),
        )
    )

    # Fetch each posting and drop the ones that are provably closed. Sorting
    # first means the verification budget is spent on the best matches.
    removed_closed = 0
    if verify_live:
        verify_started = time.perf_counter()
        jobs, removed_closed = verify_jobs(jobs)
        verified_open = sum(1 for job in jobs if job.get("verified"))
        logger.info(
            "LIVENESS finished | checked=%d | open=%d | unknown=%d | "
            "closed_removed=%d | %.2fs",
            len(jobs) + removed_closed,
            verified_open,
            len(jobs) - verified_open,
            removed_closed,
            time.perf_counter() - verify_started,
        )
    else:
        for job in jobs:
            job.setdefault("status", "unknown")
            job.setdefault("verified", False)

    # Location and experience are reported on each job, never filtered on, so
    # a search returns everything it found and the UI decides what to show.
    jobs = annotate_locations(jobs, location_filters, raw=raw_results)
    jobs = annotate_experience(jobs, bands, raw=raw_results)

    # Re-sort now that each job knows where it is: requested locations first,
    # then same-country, then unplaced, with relevance breaking ties inside
    # each group.
    if location_filters and not raw_results:
        jobs.sort(
            key=lambda j: (
                match_rank(j.get("location_match", MATCH_UNKNOWN)),
                -j["relevance_score"],
                -j["hit_count"],
                j["title"].lower(),
            )
        )

    # Stable order for queries used
    queries_used.sort(key=lambda q: (q["source_name"], q["label"]))

    response = {
        "total": len(jobs),
        "jobs": jobs,
        "queries_used": queries_used,
        "query_count": len(queries_used),
        "removed_closed": removed_closed,
        "search_providers": sorted(providers_seen),
        "google_enabled": google_search_available(),
        "raw_results": raw_results,
        "variables": variables,
    }
    logger.info(
        "JOB SEARCH finished | jobs=%d | closed_removed=%d | "
        "queries_executed=%d | providers=%s | %.2fs",
        len(jobs),
        removed_closed,
        len(queries_used),
        ",".join(sorted(providers_seen)) or "none",
        time.perf_counter() - search_started,
    )
    return response
