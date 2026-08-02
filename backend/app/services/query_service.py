from datetime import datetime, timezone

from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from app.models import Collection, Query
from app.schemas import QueryCreate, QueryUpdate
from app.services.template_service import google_search_url, resolve_template


def _attach_collection_name(query: Query) -> Query:
    query.collection_name = query.collection.name if query.collection else None  # type: ignore[attr-defined]
    return query


def list_queries(
    db: Session,
    *,
    search: str | None = None,
    category: str | None = None,
    collection_id: int | None = None,
    is_favorite: bool | None = None,
    tag: str | None = None,
) -> list[Query]:
    q = db.query(Query).options(joinedload(Query.collection))

    if search:
        like = f"%{search}%"
        q = q.filter(
            or_(
                Query.title.ilike(like),
                Query.query_text.ilike(like),
                Query.notes.ilike(like),
                Query.category.ilike(like),
            )
        )
    if category:
        q = q.filter(Query.category == category)
    if collection_id is not None:
        q = q.filter(Query.collection_id == collection_id)
    if is_favorite is not None:
        q = q.filter(Query.is_favorite == is_favorite)
    if tag:
        # SQLite JSON: simple string containment check on serialized tags
        q = q.filter(Query.tags.contains(tag))

    rows = q.order_by(Query.is_favorite.desc(), Query.updated_at.desc()).all()
    return [_attach_collection_name(r) for r in rows]


def get_query(db: Session, query_id: int) -> Query | None:
    row = (
        db.query(Query)
        .options(joinedload(Query.collection))
        .filter(Query.id == query_id)
        .first()
    )
    if row:
        return _attach_collection_name(row)
    return None


def create_query(db: Session, data: QueryCreate) -> Query:
    row = Query(**data.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return get_query(db, row.id)  # type: ignore[return-value]


def update_query(db: Session, query_id: int, data: QueryUpdate) -> Query | None:
    row = db.query(Query).filter(Query.id == query_id).first()
    if not row:
        return None
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(row, key, value)
    row.updated_at = datetime.now(timezone.utc)
    db.commit()
    return get_query(db, query_id)


def delete_query(db: Session, query_id: int) -> bool:
    row = db.query(Query).filter(Query.id == query_id).first()
    if not row:
        return False
    db.delete(row)
    db.commit()
    return True


def record_open(
    db: Session,
    query_id: int,
    variables: dict[str, str] | None = None,
) -> dict | None:
    row = get_query(db, query_id)
    if not row:
        return None

    variables = variables or {}
    resolved, _ = resolve_template(row.query_text, variables)
    url = google_search_url(resolved)

    row.open_count += 1
    row.last_opened = datetime.now(timezone.utc)
    db.commit()

    return {
        "id": row.id,
        "title": row.title,
        "url": url,
        "resolved_query": resolved,
    }


def bulk_open(
    db: Session,
    ids: list[int],
    variables: dict[str, str] | None = None,
) -> list[dict]:
    results = []
    for qid in ids:
        result = record_open(db, qid, variables)
        if result:
            results.append(result)
    return results


def list_collections(db: Session) -> list[Collection]:
    collections = db.query(Collection).order_by(Collection.name).all()
    for c in collections:
        c.query_count = len(c.queries)  # type: ignore[attr-defined]
    return collections


def get_or_create_collection(db: Session, name: str) -> Collection:
    existing = db.query(Collection).filter(Collection.name == name).first()
    if existing:
        return existing
    c = Collection(name=name)
    db.add(c)
    db.commit()
    db.refresh(c)
    return c
