from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

from app.database import get_db
from app.models import Report, Client, ReportFormat, ReportFrequency, ReportStatus, User
from app.routes.auth import get_current_user
from app.security.tenancy import get_owned_client, get_owned_report

router = APIRouter(prefix="/reports", tags=["Reports"])


# ── Schemas ───────────────────────────────────────────────────────────────────

class ReportCreate(BaseModel):
    client_id: int
    title: str
    frequency: ReportFrequency = ReportFrequency.manual
    format: ReportFormat = ReportFormat.pdf
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    platforms: Optional[List[str]] = None
    kpi_config: Optional[Dict[str, Any]] = None


class ReportResponse(BaseModel):
    id: int
    client_id: int
    title: str
    frequency: ReportFrequency
    format: ReportFormat
    status: ReportStatus
    date_from: Optional[datetime]
    date_to: Optional[datetime]
    platforms: Optional[List[str]]
    file_url: Optional[str]
    error_message: Optional[str]
    generated_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


# ── Background task ───────────────────────────────────────────────────────────

def _generate_report_task(report_id: int, db_url: str):
    """Placeholder — replaced by Celery task in production."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    engine = create_engine(db_url)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    try:
        report = db.query(Report).filter(Report.id == report_id).first()
        if report:
            report.status = ReportStatus.completed
            report.generated_at = datetime.utcnow()
            report.file_url = f"/reports/{report_id}/download"
            db.commit()
    finally:
        db.close()


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("/", response_model=List[ReportResponse])
def list_reports(
    client_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(Report).join(Client).filter(Client.owner_id == current_user.id)
    if client_id:
        query = query.filter(Report.client_id == client_id)
    return query.order_by(Report.created_at.desc()).offset(skip).limit(limit).all()


@router.post("/", response_model=ReportResponse, status_code=201)
def create_report(
    payload: ReportCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # get_owned_client enforces tenant isolation on the target client
    client = db.query(Client).filter(
        Client.id == payload.client_id,
        Client.owner_id == current_user.id,
        Client.is_active == True,
    ).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    report = Report(**payload.model_dump(), status=ReportStatus.pending)
    db.add(report)
    db.commit()
    db.refresh(report)

    from app.config import settings
    background_tasks.add_task(_generate_report_task, report.id, settings.database_url)
    return report


@router.get("/{report_id}", response_model=ReportResponse)
def get_report(report: Report = Depends(get_owned_report)):
    return report


@router.delete("/{report_id}", status_code=204)
def delete_report(
    report: Report = Depends(get_owned_report),
    db: Session = Depends(get_db),
):
    db.delete(report)
    db.commit()


@router.get("/{report_id}/status")
def get_report_status(report: Report = Depends(get_owned_report)):
    return {
        "id": report.id,
        "status": report.status,
        "generated_at": report.generated_at,
        "file_url": report.file_url,
        "error_message": report.error_message,
    }
