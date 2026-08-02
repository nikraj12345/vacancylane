from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Collection
from app.schemas import CollectionCreate, CollectionOut, CollectionUpdate
from app.services import query_service

router = APIRouter(prefix="/collections", tags=["collections"])


@router.get("", response_model=list[CollectionOut])
def list_collections(db: Session = Depends(get_db)):
    return query_service.list_collections(db)


@router.post("", response_model=CollectionOut, status_code=201)
def create_collection(data: CollectionCreate, db: Session = Depends(get_db)):
    existing = db.query(Collection).filter(Collection.name == data.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Collection already exists")
    row = Collection(**data.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    row.query_count = 0  # type: ignore[attr-defined]
    return row


@router.put("/{collection_id}", response_model=CollectionOut)
def update_collection(
    collection_id: int,
    data: CollectionUpdate,
    db: Session = Depends(get_db),
):
    row = db.query(Collection).filter(Collection.id == collection_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Collection not found")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(row, key, value)
    db.commit()
    db.refresh(row)
    row.query_count = len(row.queries)  # type: ignore[attr-defined]
    return row


@router.delete("/{collection_id}", status_code=204)
def delete_collection(collection_id: int, db: Session = Depends(get_db)):
    row = db.query(Collection).filter(Collection.id == collection_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Collection not found")
    db.delete(row)
    db.commit()
