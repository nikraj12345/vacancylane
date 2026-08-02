from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import JobApplication, User
from app.services.auth import get_current_user

router = APIRouter(prefix="/applications", tags=["applications"])


class ApplyRequest(BaseModel):
    job_url: str = Field(..., min_length=8, max_length=2000)
    job_title: str = Field(..., min_length=1, max_length=500)
    company: str | None = Field(default=None, max_length=255)
    location: str | None = Field(default=None, max_length=255)
    source: str | None = Field(default=None, max_length=100)
    source_name: str | None = Field(default=None, max_length=100)
    notes: str | None = Field(default=None, max_length=2000)


class ApplicationResponse(BaseModel):
    id: int
    job_url: str
    job_title: str
    company: str | None = None
    location: str | None = None
    source: str | None = None
    source_name: str | None = None
    status: str
    applied_at: datetime
    notes: str | None = None

    model_config = {"from_attributes": True}


class ApplicationListResponse(BaseModel):
    total: int
    applications: list[ApplicationResponse]


@router.get("", response_model=ApplicationListResponse)
def list_applications(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = (
        db.query(JobApplication)
        .filter(JobApplication.user_id == user.id)
        .order_by(JobApplication.applied_at.desc())
        .all()
    )
    return ApplicationListResponse(
        total=len(rows),
        applications=[ApplicationResponse.model_validate(row) for row in rows],
    )


@router.post("", response_model=ApplicationResponse, status_code=status.HTTP_201_CREATED)
def apply_to_job(
    payload: ApplyRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    existing = (
        db.query(JobApplication)
        .filter(
            JobApplication.user_id == user.id,
            JobApplication.job_url == payload.job_url,
        )
        .one_or_none()
    )
    if existing:
        return ApplicationResponse.model_validate(existing)

    row = JobApplication(
        user_id=user.id,
        job_url=str(payload.job_url),
        job_title=payload.job_title.strip(),
        company=(payload.company or None),
        location=(payload.location or None),
        source=(payload.source or None),
        source_name=(payload.source_name or None),
        notes=(payload.notes or None),
        status="applied",
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return ApplicationResponse.model_validate(row)


class ApplicationUpdateRequest(BaseModel):
    status: str | None = Field(default=None, max_length=40)
    notes: str | None = Field(default=None, max_length=2000)


@router.patch("/{application_id}", response_model=ApplicationResponse)
def update_application(
    application_id: int,
    payload: ApplicationUpdateRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    row = (
        db.query(JobApplication)
        .filter(
            JobApplication.id == application_id,
            JobApplication.user_id == user.id,
        )
        .one_or_none()
    )
    if row is None:
        raise HTTPException(status_code=404, detail="Application not found")
    if payload.status is not None:
        allowed = {"applied", "interviewing", "offer", "rejected", "withdrawn"}
        if payload.status not in allowed:
            raise HTTPException(status_code=400, detail="Invalid status")
        row.status = payload.status
    if payload.notes is not None:
        row.notes = payload.notes
    db.commit()
    db.refresh(row)
    return ApplicationResponse.model_validate(row)


@router.delete("/{application_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_application(
    application_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    row = (
        db.query(JobApplication)
        .filter(
            JobApplication.id == application_id,
            JobApplication.user_id == user.id,
        )
        .one_or_none()
    )
    if row is None:
        raise HTTPException(status_code=404, detail="Application not found")
    db.delete(row)
    db.commit()
