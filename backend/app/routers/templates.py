from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import AtsPreset
from app.schemas import (
    AtsPresetOut,
    ExportPayload,
    ImportRequest,
    ImportResponse,
    ResolveTemplateRequest,
    ResolveTemplateResponse,
)
from app.services.export_service import export_queries, import_queries
from app.services.template_service import extract_variables, google_search_url, resolve_template

router = APIRouter(tags=["templates"])


@router.get("/presets", response_model=list[AtsPresetOut])
def list_presets(db: Session = Depends(get_db)):
    return db.query(AtsPreset).order_by(AtsPreset.name).all()


@router.post("/templates/resolve", response_model=ResolveTemplateResponse)
def resolve(data: ResolveTemplateRequest):
    resolved, missing = resolve_template(data.template, data.variables)
    return ResolveTemplateResponse(
        resolved=resolved,
        url=google_search_url(resolved),
        missing_variables=missing or extract_variables(resolved),
    )


@router.get("/export", response_model=ExportPayload)
def export_all(db: Session = Depends(get_db)):
    return export_queries(db)


@router.post("/import", response_model=ImportResponse)
def import_all(data: ImportRequest, db: Session = Depends(get_db)):
    return import_queries(db, data)
