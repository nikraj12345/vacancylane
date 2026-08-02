from datetime import datetime, timezone
import uuid

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    JSON,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    google_sub: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, nullable=False, index=True)
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    picture_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    last_login_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    applications: Mapped[list["JobApplication"]] = relationship(
        "JobApplication", back_populates="user", cascade="all, delete-orphan"
    )
    saved_searches: Mapped[list["SavedSearch"]] = relationship(
        "SavedSearch", back_populates="user", cascade="all, delete-orphan"
    )


class JobApplication(Base):
    __tablename__ = "job_applications"
    __table_args__ = (
        UniqueConstraint("user_id", "job_url", name="uq_user_job_url"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    job_url: Mapped[str] = mapped_column(Text, nullable=False)
    job_title: Mapped[str] = mapped_column(String(500), nullable=False)
    company: Mapped[str | None] = mapped_column(String(255), nullable=True)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    source: Mapped[str | None] = mapped_column(String(100), nullable=True)
    source_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(String(40), default="applied", index=True)
    applied_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    user: Mapped[User] = relationship("User", back_populates="applications")


class SavedSearch(Base):
    """A search a signed-in user ran — so they can replay previous queries."""

    __tablename__ = "saved_searches"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    role: Mapped[str] = mapped_column(String(200), nullable=False)
    alternate_role: Mapped[str | None] = mapped_column(String(200), nullable=True)
    location_label: Mapped[str | None] = mapped_column(String(500), nullable=True)
    skills: Mapped[str | None] = mapped_column(Text, nullable=True)
    company: Mapped[str | None] = mapped_column(String(255), nullable=True)
    experience_bands: Mapped[list] = mapped_column(JSON, default=list)
    sources: Mapped[list] = mapped_column(JSON, default=list)
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    result_count: Mapped[int] = mapped_column(Integer, default=0)
    results_json: Mapped[list] = mapped_column(JSON, default=list, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, index=True
    )

    user: Mapped[User] = relationship("User", back_populates="saved_searches")


class Collection(Base):
    __tablename__ = "collections"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    color: Mapped[str] = mapped_column(String(20), default="#007acc")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    queries: Mapped[list["Query"]] = relationship("Query", back_populates="collection")


class Query(Base):
    __tablename__ = "queries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    query_text: Mapped[str] = mapped_column(Text, nullable=False)
    tags: Mapped[list] = mapped_column(JSON, default=list)
    is_favorite: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    collection_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("collections.id"), nullable=True, index=True
    )
    open_count: Mapped[int] = mapped_column(Integer, default=0)
    last_opened: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )

    collection: Mapped[Collection | None] = relationship("Collection", back_populates="queries")


class AtsPreset(Base):
    __tablename__ = "ats_presets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    slug: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    query_template: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
