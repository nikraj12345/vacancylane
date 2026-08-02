from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import BulkOpenRequest, BulkOpenResponse, OpenResult
from app.services import query_service

router = APIRouter(tags=["bulk"])


@router.post("/bulk-open", response_model=BulkOpenResponse)
def bulk_open(data: BulkOpenRequest, db: Session = Depends(get_db)):
    results = query_service.bulk_open(db, data.ids, data.variables)
    return BulkOpenResponse(results=[OpenResult(**r) for r in results])
