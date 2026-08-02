import logging

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel, Field
import anyio
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.services.auth import get_optional_user
from app.services.job_search_service import (
    ATS_SITES,
    build_google_search_links,
    search_jobs,
)
from app.services.google_search import google_providers_configured, google_search_available
from app.services.resume_parser import parse_resume
from app.services.search_history import persist_from_job_search

logger = logging.getLogger("uvicorn.error")

router = APIRouter(tags=["search"])


class LocationFilter(BaseModel):
    """A single location the user picked, in structured form.

    The dork clause alone cannot be matched reliably against ATS locations,
    which is why the city/country parts are sent separately.
    """

    label: str = ""
    city: str = ""
    state: str = ""
    country: str = ""
    remote: bool = False


class JobSearchRequest(BaseModel):
    role: str = Field(..., min_length=1, max_length=200)
    location: str = ""
    locations: list[LocationFilter] = Field(default_factory=list)
    skills: str = ""
    experience: str = ""
    experience_bands: list[str] = Field(default_factory=list)
    alternate_role: str = ""
    company: str = ""
    sources: list[str] | None = None
    max_per_source: int = Field(default=8, ge=1, le=20)
    date_posted: str = Field(
        default="month", pattern="^(any|day|week|month|year)$"
    )
    remote_only: bool = False
    employment_type: str = Field(
        default="",
        pattern="^(|Full-time|Part-time|Contract)$",
    )
    verify_live: bool = True
    # Show everything search returned: no liveness, location, experience or
    # relevance filtering.
    raw_results: bool = False


class JobListing(BaseModel):
    title: str
    url: str
    snippet: str
    source: str
    source_name: str
    company: str | None = None
    location: str | None = None
    location_match: str = "unknown"
    location_hint: str | None = None
    is_remote: bool = False
    employment_type: str | None = None
    experience_match: str = "unknown"
    experience_years: str | None = None
    posted_text: str | None = None
    posted_at: str | None = None
    relevance_score: int
    hit_count: int = 1
    matched_queries: list[str] = Field(default_factory=list)
    status: str = "unknown"
    verified: bool = False


class QueryUsed(BaseModel):
    source: str
    source_name: str
    label: str = ""
    query: str


class JobSearchResponse(BaseModel):
    total: int
    jobs: list[JobListing]
    queries_used: list[QueryUsed]
    query_count: int = 0
    removed_closed: int = 0
    search_providers: list[str] = Field(default_factory=list)
    google_enabled: bool = False
    raw_results: bool = False
    variables: dict[str, str]


class SearchStatusResponse(BaseModel):
    google_enabled: bool
    providers: list[str]
    setup_hint: str


class GoogleLink(BaseModel):
    source: str
    source_name: str
    label: str
    query: str
    google_url: str


class GoogleLinksResponse(BaseModel):
    combined_query: str
    combined_google_url: str
    links: list[GoogleLink]
    count: int


class ResumeLocation(BaseModel):
    label: str
    city: str = ""
    state: str = ""
    country: str = ""
    remote: bool = False


class ResumeProfileResponse(BaseModel):
    role: str = ""
    alternate_role: str = ""
    skills: list[str] = Field(default_factory=list)
    skills_text: str = ""
    experience_years: float | None = None
    experience_bands: list[str] = Field(default_factory=list)
    locations: list[ResumeLocation] = Field(default_factory=list)
    summary: str = ""
    warnings: list[str] = Field(default_factory=list)


@router.get("/ats-sources")
def list_ats_sources():
    return [
        {"slug": slug, "name": meta["name"]}
        for slug, meta in ATS_SITES.items()
    ]


@router.post("/search/from-resume", response_model=ResumeProfileResponse)
async def search_from_resume(file: UploadFile = File(...)):
    """Parse an uploaded resume into the same fields the search form uses."""
    content = await file.read()
    try:
        profile = parse_resume(file.filename or "resume.txt", content)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return profile.as_dict()


@router.get("/search/status", response_model=SearchStatusResponse)
def search_status():
    """Whether Google results are wired into the search pipeline."""
    providers = google_providers_configured()
    if providers:
        hint = (
            "Google organic results are active via "
            + ", ".join(providers)
            + "."
        )
    else:
        hint = (
            "Add SERPER_API_KEY to backend/.env (free 2,500 queries at "
            "https://serper.dev) to pull real Google results into the app."
        )
    return {
        "google_enabled": google_search_available(),
        "providers": providers,
        "setup_hint": hint,
    }


@router.post("/search/google-links", response_model=GoogleLinksResponse)
def google_links(
    data: JobSearchRequest,
    user: User | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
):
    """Build google.com search URLs for the same ATS dork queries."""
    if data.sources:
        unknown = [s for s in data.sources if s not in ATS_SITES]
        if unknown:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown ATS sources: {', '.join(unknown)}",
            )

    result = build_google_search_links(
        role=data.role,
        location=data.location,
        skills=data.skills,
        experience=data.experience,
        experience_bands=data.experience_bands,
        alternate_role=data.alternate_role,
        company=data.company,
        sources=data.sources,
        date_posted=data.date_posted,
        remote_only=data.remote_only,
        employment_type=data.employment_type,
    )
    if user is not None:
        try:
            persist_from_job_search(
                db,
                user,
                data,
                result_count=int(result.get("count") or 0),
            )
        except Exception:
            logger.exception("Failed to persist search history from google-links")
    return result


@router.post("/search", response_model=JobSearchResponse)
async def search(
    data: JobSearchRequest,
    user: User | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
):
    if data.sources:
        unknown = [s for s in data.sources if s not in ATS_SITES]
        if unknown:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown ATS sources: {', '.join(unknown)}",
            )

    def _run():
        return search_jobs(
            role=data.role,
            location=data.location,
            skills=data.skills,
            experience=data.experience,
            experience_bands=data.experience_bands,
            alternate_role=data.alternate_role,
            company=data.company,
            sources=data.sources,
            max_per_source=data.max_per_source,
            date_posted=data.date_posted,
            remote_only=data.remote_only,
            employment_type=data.employment_type,
            verify_live=data.verify_live,
            location_filters=[
                item.model_dump() for item in data.locations
            ],
            raw_results=data.raw_results,
        )

    # Keep FastAPI event loop free while ThreadPoolExecutor does I/O-bound search
    result = await anyio.to_thread.run_sync(_run)

    # History must not depend on a separate frontend fire-and-forget call.
    if user is not None:
        try:
            persist_from_job_search(
                db,
                user,
                data,
                result_count=int(result.get("total") or 0),
            )
        except Exception:
            logger.exception("Failed to persist search history")

    return result
