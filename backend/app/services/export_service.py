from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models import Query
from app.schemas import ExportPayload, ExportQuery, ImportRequest, ImportResponse
from app.services.query_service import get_or_create_collection


def export_queries(db: Session) -> ExportPayload:
    rows = db.query(Query).all()
    queries = [
        ExportQuery(
            title=r.title,
            category=r.category,
            query_text=r.query_text,
            tags=r.tags or [],
            is_favorite=r.is_favorite,
            notes=r.notes,
            collection=r.collection.name if r.collection else None,
        )
        for r in rows
    ]
    return ExportPayload(
        version=1,
        exported_at=datetime.now(timezone.utc),
        queries=queries,
    )


def import_queries(db: Session, payload: ImportRequest) -> ImportResponse:
    imported = 0
    skipped = 0
    details: list[dict] = []

    for item in payload.queries:
        existing = (
            db.query(Query)
            .filter(Query.title == item.title, Query.query_text == item.query_text)
            .first()
        )
        if existing and payload.merge:
            skipped += 1
            details.append({"title": item.title, "status": "skipped"})
            continue

        collection_id = None
        if item.collection:
            collection = get_or_create_collection(db, item.collection)
            collection_id = collection.id

        row = Query(
            title=item.title,
            category=item.category,
            query_text=item.query_text,
            tags=item.tags,
            is_favorite=item.is_favorite,
            notes=item.notes,
            collection_id=collection_id,
        )
        db.add(row)
        imported += 1
        details.append({"title": item.title, "status": "imported"})

    db.commit()
    return ImportResponse(imported=imported, skipped=skipped, details=details)
