from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import (
    BulkOpenRequest,
    BulkOpenResponse,
    OpenRequest,
    OpenResult,
    QueryCreate,
    QueryOut,
    QueryUpdate,
)
from app.services import query_service

router = APIRouter(prefix="/queries", tags=["queries"])


@router.get("", response_model=list[QueryOut])
def list_queries(
    search: str | None = None,
    category: str | None = None,
    collection_id: int | None = None,
    is_favorite: bool | None = None,
    tag: str | None = None,
    db: Session = Depends(get_db),
):
    return query_service.list_queries(
        db,
        search=search,
        category=category,
        collection_id=collection_id,
        is_favorite=is_favorite,
        tag=tag,
    )


@router.post("", response_model=QueryOut, status_code=201)
def create_query(data: QueryCreate, db: Session = Depends(get_db)):
    return query_service.create_query(db, data)


@router.get("/{query_id}", response_model=QueryOut)
def get_query(query_id: int, db: Session = Depends(get_db)):
    row = query_service.get_query(db, query_id)
    if not row:
        raise HTTPException(status_code=404, detail="Query not found")
    return row


@router.put("/{query_id}", response_model=QueryOut)
def update_query(query_id: int, data: QueryUpdate, db: Session = Depends(get_db)):
    row = query_service.update_query(db, query_id, data)
    if not row:
        raise HTTPException(status_code=404, detail="Query not found")
    return row


@router.delete("/{query_id}", status_code=204)
def delete_query(query_id: int, db: Session = Depends(get_db)):
    if not query_service.delete_query(db, query_id):
        raise HTTPException(status_code=404, detail="Query not found")


@router.post("/{query_id}/open", response_model=OpenResult)
def open_query(
    query_id: int,
    data: OpenRequest | None = None,
    db: Session = Depends(get_db),
):
    variables = data.variables if data else {}
    result = query_service.record_open(db, query_id, variables)
    if not result:
        raise HTTPException(status_code=404, detail="Query not found")
    return result
