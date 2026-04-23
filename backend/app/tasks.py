from app.celery_app import celery_app
from app.database import SessionLocal
from app.models import Report, ReportStatus, ReportFrequency
from datetime import datetime


@celery_app.task(bind=True, name="app.tasks.generate_report")
def generate_report(self, report_id: int):
    """Generate a single report asynchronously."""
    db = SessionLocal()
    try:
        report = db.query(Report).filter(Report.id == report_id).first()
        if not report:
            return {"error": "Report not found"}

        report.status = ReportStatus.processing
        db.commit()

        # TODO: call platform services, build PDF/Excel/PPT
        # Placeholder: mark as completed
        report.status = ReportStatus.completed
        report.generated_at = datetime.utcnow()
        report.file_url = f"/reports/{report_id}/download"
        db.commit()

        return {"status": "completed", "report_id": report_id}
    except Exception as exc:
        db.query(Report).filter(Report.id == report_id).update({
            "status": ReportStatus.failed,
            "error_message": str(exc),
        })
        db.commit()
        raise self.retry(exc=exc, countdown=60, max_retries=3)
    finally:
        db.close()


@celery_app.task(name="app.tasks.run_scheduled_reports")
def run_scheduled_reports():
    """Trigger generation for all scheduled (non-manual) reports."""
    db = SessionLocal()
    try:
        reports = (
            db.query(Report)
            .filter(Report.frequency != ReportFrequency.manual)
            .all()
        )
        for report in reports:
            generate_report.delay(report.id)
        return {"triggered": len(reports)}
    finally:
        db.close()
