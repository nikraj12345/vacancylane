"""Verify that discovered job postings are still open.

Search engines keep indexing ATS pages long after a role is filled, so every
candidate URL is checked before it reaches the user.

Two strategies, in order of confidence:

1. Public ATS APIs. Greenhouse, Lever, Ashby and SmartRecruiters all expose the
   set of currently-open postings, which is authoritative. Board-wide endpoints
   are fetched once per company and cached for the request.
2. Fetching the page itself and looking at the status code, any redirect away
   from the posting id, and closed/open markers in the HTML.

Anything we cannot prove is closed is kept, so a flaky network never silently
hides real jobs.
"""

from __future__ import annotations

import re
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from threading import BoundedSemaphore, Lock
from urllib.parse import parse_qs, urlparse

import httpx

STATUS_OPEN = "open"
STATUS_CLOSED = "closed"
STATUS_UNKNOWN = "unknown"

DEAD_STATUSES = {404, 410}
# Bot walls and rate limits tell us nothing about the posting itself.
INCONCLUSIVE_STATUSES = {401, 403, 405, 408, 429}

# Only read the head of the document; ATS pages inline large JSON payloads.
MAX_BODY_BYTES = 150_000
REQUEST_TIMEOUT = 6.0
MAX_WORKERS = 24

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/122.0 Safari/537.36"
)

CLOSED_MARKERS = (
    "no longer accepting application",
    "not accepting applications",
    "no longer available",
    "no longer active",
    "no longer accepting",
    "no longer open",
    "no longer being accepted",
    "this job is closed",
    "this posting is closed",
    "job posting is closed",
    "posting is no longer",
    "position has been filled",
    "role has been filled",
    "position is closed",
    "applications are closed",
    "application period has ended",
    "this job has expired",
    "job has expired",
    "posting has expired",
    "job not found",
    "posting not found",
    "position not found",
    "page not found",
    "404 - not found",
    "oops! we couldn't find",
    "sorry, this job",
    "job you are looking for",
    "opening is closed",
    "vacancy is closed",
    "this position is no longer",
)

# A rendered application form means the posting is open, even when the page
# boilerplate happens to contain one of the phrases above.
OPEN_MARKERS = (
    "apply for this job",
    "submit application",
    "submit your application",
    "apply now",
    "application form",
    "attach resume",
    "attach your resume",
    "autofill with greenhouse",
    "start your application",
)

# Client-rendered boards: a 200 with an empty shell proves nothing, so only
# status codes, redirects and inlined JSON are trusted.
SPA_SOURCES = {"workday", "ashby"}

# Boards that publish every open posting in one company-wide request.
BOARD_SOURCES = {"greenhouse", "ashby"}

# Firing the whole wave at one company's tenant gets us rate limited, which
# looks identical to "unknown" and needlessly hides live jobs.
MAX_REQUESTS_PER_HOST = 3
RETRY_AFTER_SECONDS = 0.75

_host_locks_guard = Lock()
_host_locks: dict[str, BoundedSemaphore] = {}


def _host_gate(url: str) -> BoundedSemaphore:
    host = urlparse(url).netloc.lower()
    with _host_locks_guard:
        gate = _host_locks.get(host)
        if gate is None:
            gate = BoundedSemaphore(MAX_REQUESTS_PER_HOST)
            _host_locks[host] = gate
        return gate


def _get(client: httpx.Client, url: str, **kwargs) -> httpx.Response:
    """GET with per-host throttling and one retry when rate limited."""
    with _host_gate(url):
        response = client.get(url, **kwargs)
        if response.status_code in {403, 429}:
            time.sleep(RETRY_AFTER_SECONDS)
            response = client.get(url, **kwargs)
        return response

UUID_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.I
)
SKIP_SEGMENTS = {"jobs", "job", "careers", "apply", "en-us", "embed", "j", "o"}


@dataclass
class PostingInfo:
    """What the ATS itself says about a posting."""

    status: str
    location: str | None = None
    is_remote: bool | None = None
    employment_type: str | None = None
    title: str | None = None
    posted_at: str | None = None


@dataclass
class BoardEntry:
    """A single open posting as listed by a company-wide board endpoint."""

    title: str = ""
    location: str = ""
    is_remote: bool | None = None
    employment_type: str | None = None


@dataclass
class Board:
    """Open postings for one company, keyed by posting id."""

    entries: dict[str, BoardEntry] = field(default_factory=dict)


class BoardCache:
    """Per-request cache of company-wide open-posting listings."""

    def __init__(self) -> None:
        self._data: dict[tuple[str, str], Board | None] = {}
        self._lock = Lock()

    def get(self, key: tuple[str, str]) -> Board | None:
        with self._lock:
            return self._data.get(key)

    def set(self, key: tuple[str, str], value: Board | None) -> None:
        with self._lock:
            self._data[key] = value


def _path_parts(url: str) -> list[str]:
    return [part for part in urlparse(url).path.split("/") if part]


def _job_token(url: str) -> str | None:
    """The path segment that identifies the individual posting."""
    parts = _path_parts(url)
    if not parts:
        return None
    for part in reversed(parts):
        lowered = part.lower()
        if lowered in SKIP_SEGMENTS:
            continue
        if lowered.isdigit() or any(char.isdigit() for char in lowered):
            return lowered
        if len(lowered) >= 8:
            return lowered
    return parts[-1].lower()


def parse_posting(url: str, source: str) -> tuple[str, str] | None:
    """Return (company/board slug, posting id) for API-backed sources."""
    parts = _path_parts(url)
    query = parse_qs(urlparse(url).query)

    if source == "greenhouse":
        board = query.get("for", [None])[0]
        token = query.get("gh_jid", [None])[0] or query.get("token", [None])[0]
        if board and token:
            return board, token
        if len(parts) >= 2 and parts[0] != "embed":
            job_id = next(
                (part for part in reversed(parts) if part.isdigit()), None
            )
            if job_id:
                return parts[0], job_id
        return None

    if source in {"lever", "ashby"}:
        if len(parts) >= 2 and UUID_RE.match(parts[1]):
            return parts[0], parts[1].lower()
        return None

    if source == "smartrecruiters":
        if len(parts) >= 2:
            match = re.match(r"^(\d+)", parts[1])
            if match:
                return parts[0], match.group(1)
        return None

    if source == "workable":
        # apply.workable.com/<account>/j/<SHORTCODE>/
        if len(parts) >= 2:
            shortcode = next(
                (
                    part
                    for part in reversed(parts)
                    if re.fullmatch(r"[0-9A-F]{8,12}", part.upper())
                ),
                None,
            )
            if shortcode:
                return parts[0], shortcode.upper()
        return None

    if source == "workday":
        # <tenant>.<wdN>.myworkdayjobs.com/[lang/]<site>/job/<path...>
        if "job" not in parts:
            return None
        index = parts.index("job")
        if index == 0:
            return None
        site = parts[index - 1]
        remainder = "/".join(parts[index:])
        return site, remainder

    return None


def _workday_api_url(url: str) -> str | None:
    """Workday's CXS endpoint mirrors the public posting path."""
    parsed = urlparse(url)
    host = parsed.netloc
    tenant = host.split(".")[0]
    posting = parse_posting(url, "workday")
    if not tenant or not posting:
        return None
    site, remainder = posting
    return f"https://{host}/wday/cxs/{tenant}/{site}/{remainder}"


def _clean_location(value: str | None) -> str | None:
    if not value:
        return None
    cleaned = re.sub(r"\s+", " ", str(value)).strip(" ,-|")
    return cleaned or None


def _fetch_board(
    client: httpx.Client, source: str, company: str
) -> Board | None:
    """Every open posting for a company, or None when the board is unavailable."""
    try:
        if source == "greenhouse":
            response = _get(
                client,
                f"https://boards-api.greenhouse.io/v1/boards/{company}/jobs",
            )
            if response.status_code != 200:
                return None
            board = Board()
            for job in response.json().get("jobs", []):
                if job.get("id") is None:
                    continue
                location = _clean_location(
                    (job.get("location") or {}).get("name")
                )
                board.entries[str(job["id"])] = BoardEntry(
                    title=job.get("title", ""),
                    location=location or "",
                    is_remote=(
                        bool(location and "remote" in location.lower())
                        if location
                        else None
                    ),
                )
            return board

        if source == "ashby":
            response = _get(
                client,
                f"https://api.ashbyhq.com/posting-api/job-board/{company}",
            )
            if response.status_code != 200:
                return None
            board = Board()
            for job in response.json().get("jobs", []):
                if not job.get("id"):
                    continue
                locations = [job.get("location")]
                locations += [
                    secondary.get("location")
                    for secondary in job.get("secondaryLocations") or []
                ]
                joined = ", ".join(
                    part for part in (_clean_location(x) for x in locations) if part
                )
                board.entries[str(job["id"]).lower()] = BoardEntry(
                    title=job.get("title", ""),
                    location=joined,
                    is_remote=job.get("isRemote"),
                    employment_type=_normalize_employment(
                        job.get("employmentType")
                    ),
                )
            return board
    except Exception:
        return None
    return None


def _normalize_employment(value: str | None) -> str | None:
    if not value:
        return None
    text = str(value).replace("_", " ").replace("-", " ").strip().lower()
    mapping = {
        "fulltime": "Full-time",
        "full time": "Full-time",
        "parttime": "Part-time",
        "part time": "Part-time",
        "contract": "Contract",
        "contractor": "Contract",
        "temporary": "Contract",
        "intern": "Internship",
        "internship": "Internship",
    }
    return mapping.get(text.replace(" ", "") , mapping.get(text))


def _posting_api_url(
    source: str, company: str, job_id: str, url: str
) -> str | None:
    if source == "lever":
        return f"https://api.lever.co/v0/postings/{company}/{job_id}"
    if source == "smartrecruiters":
        return (
            "https://api.smartrecruiters.com/v1/companies/"
            f"{company}/postings/{job_id}"
        )
    if source == "workable":
        return (
            "https://apply.workable.com/api/v1/accounts/"
            f"{company}/jobs/{job_id}"
        )
    if source == "workday":
        return _workday_api_url(url)
    return None


def _parse_posting_payload(source: str, payload: dict) -> PostingInfo:
    """Turn an ATS posting response into liveness plus real posting details."""
    if source == "lever":
        categories = payload.get("categories") or {}
        locations = [categories.get("location")] + list(
            categories.get("allLocations") or []
        )
        joined = ", ".join(
            part
            for part in dict.fromkeys(
                _clean_location(x) for x in locations
            )
            if part
        )
        workplace = (payload.get("workplaceType") or "").lower()
        return PostingInfo(
            status=STATUS_OPEN,
            location=joined or None,
            is_remote=workplace == "remote" or "remote" in joined.lower(),
            employment_type=_normalize_employment(categories.get("commitment")),
            title=payload.get("text"),
        )

    if source == "smartrecruiters":
        location = payload.get("location") or {}
        parts = [
            location.get("city"),
            location.get("region"),
            location.get("country"),
        ]
        joined = ", ".join(
            part for part in (_clean_location(x) for x in parts) if part
        )
        employment = (payload.get("typeOfEmployment") or {}).get("label")
        return PostingInfo(
            status=STATUS_OPEN,
            location=joined or None,
            is_remote=bool(location.get("remote")),
            employment_type=_normalize_employment(employment),
            title=payload.get("name"),
            posted_at=payload.get("releasedDate"),
        )

    if source == "workable":
        # A posting only counts as open while Workable reports it published.
        state = (payload.get("state") or "").lower()
        if state and state not in {"published", "open"}:
            return PostingInfo(status=STATUS_CLOSED)
        location = payload.get("location") or {}
        parts = [
            location.get("city"),
            location.get("region"),
            location.get("country"),
        ]
        joined = ", ".join(
            part for part in (_clean_location(x) for x in parts) if part
        )
        return PostingInfo(
            status=STATUS_OPEN,
            location=joined or None,
            is_remote=bool(
                location.get("workplace") == "remote"
                or payload.get("remote")
                or payload.get("workplace") == "remote"
            ),
            employment_type=_normalize_employment(payload.get("employment_type")),
            title=payload.get("title"),
            posted_at=payload.get("published_on") or payload.get("created_at"),
        )

    if source == "workday":
        info = payload.get("jobPostingInfo") or {}
        if info.get("jobPostingIsClosed") or info.get("canApply") is False:
            return PostingInfo(status=STATUS_CLOSED)
        return PostingInfo(
            status=STATUS_OPEN,
            location=_clean_location(info.get("location")),
            is_remote=bool(
                info.get("remoteType")
                or "remote" in str(info.get("location", "")).lower()
            ),
            employment_type=_normalize_employment(info.get("timeType")),
            title=info.get("title"),
            posted_at=info.get("startDate"),
        )

    return PostingInfo(status=STATUS_OPEN)


def _check_posting_api(
    client: httpx.Client, source: str, company: str, job_id: str, url: str
) -> PostingInfo:
    """Per-posting API probe for boards without a company-wide endpoint."""
    api_url = _posting_api_url(source, company, job_id, url)
    if not api_url:
        return PostingInfo(status=STATUS_UNKNOWN)

    try:
        response = _get(client, api_url)
        if response.status_code == 200:
            return _parse_posting_payload(source, response.json())
        if response.status_code in DEAD_STATUSES:
            return PostingInfo(status=STATUS_CLOSED)
    except Exception:
        return PostingInfo(status=STATUS_UNKNOWN)
    return PostingInfo(status=STATUS_UNKNOWN)


def _redirected_away(original: str, final: str) -> bool:
    """A closed posting usually bounces to the company's board root."""
    if not final or original == final:
        return False
    token = _job_token(original)
    if not token or len(token) < 4:
        return False
    if token in urlparse(final).path.lower():
        return False
    # The posting id vanished from the URL: we landed on a listing or error page.
    return True


def _classify_body(body: str, source: str) -> str:
    lowered = body.lower()
    if source in SPA_SOURCES:
        for marker in CLOSED_MARKERS:
            if marker in lowered:
                return STATUS_CLOSED
        return STATUS_UNKNOWN

    has_open = any(marker in lowered for marker in OPEN_MARKERS)
    has_closed = any(marker in lowered for marker in CLOSED_MARKERS)

    if has_closed and not has_open:
        return STATUS_CLOSED
    if has_open:
        return STATUS_OPEN
    return STATUS_UNKNOWN


def check_url(client: httpx.Client, url: str, source: str = "") -> str:
    try:
        with _host_gate(url), client.stream(
            "GET", url, follow_redirects=True
        ) as response:
            if response.status_code in DEAD_STATUSES:
                return STATUS_CLOSED
            if response.status_code in INCONCLUSIVE_STATUSES:
                return STATUS_UNKNOWN
            if response.status_code >= 500:
                return STATUS_UNKNOWN
            if _redirected_away(url, str(response.url)):
                return STATUS_CLOSED

            content_type = response.headers.get("content-type", "")
            if "html" not in content_type and "json" not in content_type:
                return STATUS_UNKNOWN

            collected: list[str] = []
            size = 0
            for chunk in response.iter_text():
                collected.append(chunk)
                size += len(chunk)
                if size >= MAX_BODY_BYTES:
                    break
            return _classify_body("".join(collected), source)
    except Exception:
        return STATUS_UNKNOWN


def check_job(client: httpx.Client, job: dict, cache: BoardCache) -> PostingInfo:
    source = job.get("source", "")
    url = job["url"]
    posting = parse_posting(url, source)

    if posting:
        company, job_id = posting
        if source in BOARD_SOURCES:
            board = cache.get((source, company.lower()))
            if board is not None:
                entry = board.entries.get(job_id)
                if entry is None:
                    return PostingInfo(status=STATUS_CLOSED)
                return PostingInfo(
                    status=STATUS_OPEN,
                    location=entry.location or None,
                    is_remote=entry.is_remote,
                    employment_type=entry.employment_type,
                    title=entry.title or None,
                )
        else:
            info = _check_posting_api(client, source, company, job_id, url)
            if info.status != STATUS_UNKNOWN:
                return info

    return PostingInfo(status=check_url(client, url, source))


def verify_jobs(jobs: list[dict], *, limit: int = 250) -> tuple[list[dict], int]:
    """Drop postings proven closed. Returns (surviving jobs, removed count)."""
    if not jobs:
        return jobs, 0

    targets = jobs[:limit]
    workers = min(MAX_WORKERS, max(4, len(targets)))
    cache = BoardCache()
    found: dict[str, PostingInfo] = {}

    limits = httpx.Limits(
        max_connections=workers, max_keepalive_connections=workers
    )
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/json;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }

    try:
        with httpx.Client(
            timeout=REQUEST_TIMEOUT,
            limits=limits,
            headers=headers,
            follow_redirects=True,
        ) as client:
            with ThreadPoolExecutor(max_workers=workers) as pool:
                # One board fetch per company answers all of its postings.
                boards: set[tuple[str, str]] = set()
                for job in targets:
                    source = job.get("source", "")
                    if source not in BOARD_SOURCES:
                        continue
                    posting = parse_posting(job["url"], source)
                    if posting:
                        boards.add((source, posting[0]))

                def load_board(entry: tuple[str, str]) -> None:
                    source, company = entry
                    cache.set(
                        (source, company.lower()),
                        _fetch_board(client, source, company),
                    )

                list(pool.map(load_board, boards))

                results = pool.map(
                    lambda job: (job["url"], check_job(client, job, cache)),
                    targets,
                )
                for url, info in results:
                    found[url] = info
    except Exception:
        # Never let verification failures wipe out a search.
        return jobs, 0

    surviving: list[dict] = []
    removed = 0
    for job in jobs:
        info = found.get(job["url"], PostingInfo(status=STATUS_UNKNOWN))
        if info.status == STATUS_CLOSED:
            removed += 1
            continue

        job["status"] = info.status
        job["verified"] = info.status == STATUS_OPEN
        # The ATS is authoritative about its own posting, so its details win.
        if info.location:
            job["location"] = info.location
        if info.is_remote is not None:
            job["is_remote"] = info.is_remote
        if info.employment_type:
            job["employment_type"] = info.employment_type
        if info.title:
            job["title"] = info.title
        if info.posted_at and not job.get("posted_at"):
            job["posted_at"] = info.posted_at
        surviving.append(job)

    return surviving, removed
