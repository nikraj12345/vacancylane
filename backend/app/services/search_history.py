"""Persist and list saved searches for signed-in users."""

from __future__ import annotations

from datetime import timedelta

from sqlalchemy.orm import Session

from app.models import SavedSearch, User, utcnow

# Re-running the exact same filters within this window updates the existing
# row instead of flooding history with duplicates.
DEDUPE_WINDOW = timedelta(minutes=5)


def location_label_from_payload(payload: dict) -> str | None:
    locations = payload.get("locations") or []
    labels = [
        str(item.get("label")).strip()
        for item in locations
        if isinstance(item, dict) and item.get("label")
    ]
    if labels:
        return ", ".join(labels)
    location = (payload.get("location") or "").strip()
    return location or None


def skills_label(skills: str | None) -> str | None:
    if not skills:
        return None
    # Search payloads use OR for Google dorks; history should read naturally.
    cleaned = skills.replace(" OR ", ", ").strip()
    return cleaned or None


def persist_saved_search(
    db: Session,
    user: User,
    *,
    role: str,
    alternate_role: str | None = None,
    location_label: str | None = None,
    skills: str | None = None,
    company: str | None = None,
    experience_bands: list[str] | None = None,
    sources: list[str] | None = None,
    payload: dict | None = None,
    result_count: int = 0,
    results_json: list | None = None,
) -> SavedSearch:
    """Insert a history row, or refresh a recent identical one."""
    role = role.strip()
    alternate_role = (alternate_role or "").strip() or None
    location_label = (location_label or "").strip() or None
    skills = skills_label(skills)
    company = (company or "").strip() or None
    experience_bands = list(experience_bands or [])
    sources = list(sources or [])
    payload = dict(payload or {})

    cutoff = utcnow() - DEDUPE_WINDOW
    recent = (
        db.query(SavedSearch)
        .filter(
            SavedSearch.user_id == user.id,
            SavedSearch.role == role,
            SavedSearch.location_label == location_label,
            SavedSearch.skills == skills,
            SavedSearch.company == company,
            SavedSearch.created_at >= cutoff,
        )
        .order_by(SavedSearch.created_at.desc())
        .first()
    )
    if recent and recent.payload == payload:
        recent.result_count = result_count
        if results_json:
            recent.results_json = results_json
        recent.experience_bands = experience_bands
        recent.sources = sources
        recent.alternate_role = alternate_role
        recent.created_at = utcnow()
        db.commit()
        db.refresh(recent)
        return recent

    row = SavedSearch(
        user_id=user.id,
        role=role,
        alternate_role=alternate_role,
        location_label=location_label,
        skills=skills,
        company=company,
        experience_bands=experience_bands,
        sources=sources,
        payload=payload,
        result_count=result_count,
        results_json=results_json or [],
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def persist_from_job_search(
    db: Session,
    user: User,
    data,
    *,
    result_count: int,
    results_json: list | None = None,
) -> SavedSearch:
    """Save history from a JobSearchRequest-shaped object after a search runs."""
    payload = data.model_dump() if hasattr(data, "model_dump") else dict(data)
    return persist_saved_search(
        db,
        user,
        role=data.role,
        alternate_role=data.alternate_role or None,
        location_label=location_label_from_payload(payload),
        skills=data.skills or None,
        company=data.company or None,
        experience_bands=list(data.experience_bands or []),
        sources=list(data.sources or []),
        payload=payload,
        result_count=result_count,
        results_json=results_json or [],
    )
