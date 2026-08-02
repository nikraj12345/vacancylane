from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


# ── Collection ──────────────────────────────────────────────────────────────

class CollectionBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: str | None = None
    color: str = "#007acc"


class CollectionCreate(CollectionBase):
    pass


class CollectionUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=100)
    description: str | None = None
    color: str | None = None


class CollectionOut(CollectionBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    query_count: int = 0


# ── Query ───────────────────────────────────────────────────────────────────

class QueryBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    category: str = Field(..., min_length=1, max_length=100)
    query_text: str = Field(..., min_length=1)
    tags: list[str] = Field(default_factory=list)
    is_favorite: bool = False
    notes: str | None = None
    collection_id: int | None = None


class QueryCreate(QueryBase):
    pass


class QueryUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=255)
    category: str | None = Field(None, min_length=1, max_length=100)
    query_text: str | None = Field(None, min_length=1)
    tags: list[str] | None = None
    is_favorite: bool | None = None
    notes: str | None = None
    collection_id: int | None = None


class QueryOut(QueryBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    open_count: int
    last_opened: datetime | None
    created_at: datetime
    updated_at: datetime
    collection_name: str | None = None


# ── ATS Preset ──────────────────────────────────────────────────────────────

class AtsPresetOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    slug: str
    query_template: str
    description: str | None
    created_at: datetime


# ── Bulk / Open ─────────────────────────────────────────────────────────────

class BulkOpenRequest(BaseModel):
    ids: list[int] = Field(..., min_length=1)
    variables: dict[str, str] = Field(default_factory=dict)


class OpenResult(BaseModel):
    id: int
    title: str
    url: str
    resolved_query: str


class BulkOpenResponse(BaseModel):
    results: list[OpenResult]


class OpenRequest(BaseModel):
    variables: dict[str, str] = Field(default_factory=dict)


# ── Template resolve ────────────────────────────────────────────────────────

class ResolveTemplateRequest(BaseModel):
    template: str
    variables: dict[str, str] = Field(default_factory=dict)


class ResolveTemplateResponse(BaseModel):
    resolved: str
    url: str
    missing_variables: list[str]


# ── Import / Export ─────────────────────────────────────────────────────────

class ExportQuery(BaseModel):
    title: str
    category: str
    query_text: str
    tags: list[str] = Field(default_factory=list)
    is_favorite: bool = False
    notes: str | None = None
    collection: str | None = None


class ExportPayload(BaseModel):
    version: int = 1
    exported_at: datetime | None = None
    queries: list[ExportQuery]


class ImportRequest(BaseModel):
    queries: list[ExportQuery]
    merge: bool = True


class ImportResponse(BaseModel):
    imported: int
    skipped: int
    details: list[dict[str, Any]] = Field(default_factory=list)


# ── Categories ──────────────────────────────────────────────────────────────

CATEGORIES = [
    "AI Engineer",
    "Backend",
    "Full Stack",
    "Frontend",
    "DevOps",
    "Data Engineer",
    "ML Engineer",
    "Mobile",
    "SRE",
    "Other",
]
