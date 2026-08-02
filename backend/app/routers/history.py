from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import SavedSearch, User
from app.services.auth import get_current_user
from app.services.search_history import persist_saved_search

router = APIRouter(prefix="/history", tags=["history"])


class SaveSearchRequest(BaseModel):
    role: str = Field(..., min_length=1, max_length=200)
    alternate_role: str | None = Field(default=None, max_length=200)
    location_label: str | None = Field(default=None, max_length=500)
    skills: str | None = None
    company: str | None = Field(default=None, max_length=255)
    experience_bands: list[str] = Field(default_factory=list)
    sources: list[str] = Field(default_factory=list)
    payload: dict = Field(default_factory=dict)
    result_count: int = 0
    results_json: list = Field(default_factory=list)


class SavedSearchResponse(BaseModel):
    id: str
    role: str
    alternate_role: str | None = None
    location_label: str | None = None
    skills: str | None = None
    company: str | None = None
    experience_bands: list = []
    sources: list = []
    payload: dict = {}
    result_count: int
    results_json: list = []
    created_at: datetime

    model_config = {"from_attributes": True}


class SavedSearchListResponse(BaseModel):
    total: int
    searches: list[SavedSearchResponse]


@router.get("", response_model=SavedSearchListResponse)
def list_searches(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = 50,
):
    rows = (
        db.query(SavedSearch)
        .filter(SavedSearch.user_id == user.id)
        .order_by(SavedSearch.created_at.desc())
        .limit(min(limit, 100))
        .all()
    )
    return SavedSearchListResponse(
        total=len(rows),
        searches=[SavedSearchResponse.model_validate(row) for row in rows],
    )


@router.get("/{search_id}", response_model=SavedSearchResponse)
def get_search(
    search_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    row = (
        db.query(SavedSearch)
        .filter(SavedSearch.id == search_id, SavedSearch.user_id == user.id)
        .one_or_none()
    )
    if row is None:
        raise HTTPException(status_code=404, detail="Search not found")
    return SavedSearchResponse.model_validate(row)


@router.post("", response_model=SavedSearchResponse, status_code=status.HTTP_201_CREATED)
def save_search(
    payload: SaveSearchRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    row = persist_saved_search(
        db,
        user,
        role=payload.role,
        alternate_role=payload.alternate_role,
        location_label=payload.location_label,
        skills=payload.skills,
        company=payload.company,
        experience_bands=payload.experience_bands,
        sources=payload.sources,
        payload=payload.payload,
        result_count=payload.result_count,
        results_json=payload.results_json,
    )
    return SavedSearchResponse.model_validate(row)


@router.delete("/{search_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_search(
    search_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    row = (
        db.query(SavedSearch)
        .filter(SavedSearch.id == search_id, SavedSearch.user_id == user.id)
        .one_or_none()
    )
    if row is None:
        raise HTTPException(status_code=404, detail="Search not found")
    db.delete(row)
    db.commit()
